from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urlparse

from .models import RushSettings


@dataclass
class CapturedRequest:
    url: str
    method: str
    headers: Dict[str, str]
    body: Optional[str]
    timestamp: float


class RunReporter(Protocol):
    def log(self, message: str) -> None:
        ...

    def update(self, **fields: Any) -> None:
        ...


def _normalize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    blocked = {"cookie", "host", "content-length", "connection", "origin"}
    normalized: Dict[str, str] = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in blocked:
            continue
        normalized[key_lower] = value
    return normalized


def _extract_texts_from_payload(payload: object) -> List[str]:
    if not isinstance(payload, dict):
        return []

    texts: List[str] = []

    def add_text(value: object) -> None:
        if not isinstance(value, str):
            return
        text = value.strip()
        if text:
            texts.append(text)

    for key in ("messages", "mismatched_messages"):
        messages = payload.get(key)
        if not isinstance(messages, list):
            continue
        for msg in messages:
            if isinstance(msg, dict):
                add_text(msg.get("text"))
            else:
                add_text(msg)

    results = payload.get("results")
    if isinstance(results, list):
        for result in results:
            if not isinstance(result, dict):
                continue
            add_text(result.get("text"))
            inner_messages = result.get("messages")
            if isinstance(inner_messages, list):
                for msg in inner_messages:
                    if isinstance(msg, dict):
                        add_text(msg.get("text"))
                    else:
                        add_text(msg)

    return texts


def _extract_enrolled_map(payload: object) -> Dict[int, bool]:
    if not isinstance(payload, dict):
        return {}

    class_responses = payload.get("classResponses")
    if not isinstance(class_responses, list):
        return {}

    enrolled_map: Dict[int, bool] = {}
    for item in class_responses:
        if not isinstance(item, dict):
            continue
        class_nbr = item.get("classNbr")
        if not isinstance(class_nbr, int):
            continue
        enrolled_map[class_nbr] = bool(item.get("isEnrolled"))
    return enrolled_map


def _extract_target_classes_from_body(body: Optional[str]) -> List[int]:
    if not body:
        return []

    try:
        payload = json.loads(body)
    except Exception:
        return []

    if not isinstance(payload, dict):
        return []
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return []

    targets: List[int] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        class_nbr = section.get("classNbr")
        if isinstance(class_nbr, int):
            targets.append(class_nbr)
    return targets


def _payload_enrolled_for_targets(payload: object, target_classes: List[int]) -> bool:
    enrolled_map = _extract_enrolled_map(payload)
    if not enrolled_map:
        return False

    if target_classes:
        return all(enrolled_map.get(class_nbr, False) for class_nbr in target_classes)

    return all(enrolled_map.values())


def _summarize_round(
    results: List[Dict[str, object]],
    target_classes: List[int],
) -> Dict[str, object]:
    enrolled = False
    texts: List[str] = []

    for item in results:
        if not item.get("ok"):
            continue
        payload = item.get("response")
        if _payload_enrolled_for_targets(payload, target_classes):
            enrolled = True
        texts.extend(_extract_texts_from_payload(payload))

    seen = set()
    unique_texts: List[str] = []
    for text in texts:
        if text in seen:
            continue
        seen.add(text)
        unique_texts.append(text)

    return {"enrolled": enrolled, "texts": unique_texts}


def _choose_replay_request(captured: List[CapturedRequest]) -> CapturedRequest:
    for item in reversed(captured):
        if "IScript_Enroll" in item.url:
            return item
    for item in reversed(captured):
        if "IScript_SaveSelections" in item.url:
            return item
    return captured[-1]


def _select_page(browser: Any, page_url_keyword: str):
    all_pages = []
    for context in browser.contexts:
        all_pages.extend(context.pages)

    if not all_pages:
        return None, None

    if page_url_keyword:
        for page in all_pages:
            if page_url_keyword in page.url:
                return page.context, page

    for page in all_pages:
        if page.url and page.url != "about:blank":
            return page.context, page

    return all_pages[0].context, all_pages[0]


def _configured_class_numbers(settings: RushSettings) -> List[int]:
    return [
        course.class_nbr
        for course in settings.selected_courses
        if isinstance(course.class_nbr, int)
    ]


def _endpoint_name(url: str) -> str:
    path = urlparse(url).path
    return path.rsplit("/", 1)[-1] or path or "request"


def _effective_requests_per_second(settings: RushSettings) -> Optional[float]:
    if settings.strategy_mode == "smooth":
        return settings.smooth_requests_per_second
    if settings.strategy_mode == "burst":
        return settings.burst_rounds_per_second * settings.burst_count
    if settings.strategy_mode == "hybrid":
        burst_rps = settings.hybrid_burst_rounds_per_second * settings.hybrid_burst_count
        return max(burst_rps, settings.hybrid_smooth_requests_per_second)
    return None


def _send_replay_requests(page: Any, payload: Dict[str, Optional[str]], request_count: int) -> List[Dict[str, object]]:
    return page.evaluate(
        """
        async ({req, requestCount}) => {
            const jobs = [];
            for (let i = 0; i < requestCount; i += 1) {
                jobs.push(
                    fetch(req.url, {
                        method: req.method,
                        headers: req.headers,
                        body: req.body,
                        credentials: "include",
                        mode: "cors",
                    })
                    .then(async (response) => {
                        const text = await response.text();
                        let parsed = text;
                        try { parsed = JSON.parse(text); } catch (_) {}
                        return { status: response.status, ok: response.ok, response: parsed };
                    })
                    .catch((error) => ({ status: null, ok: false, response: String(error) }))
                );
            }
            return Promise.all(jobs);
        }
        """,
        {"req": payload, "requestCount": request_count},
    )


def _handle_replay_results(
    results: List[Dict[str, object]],
    target_classes: List[int],
    request_no: int,
    reporter: RunReporter,
) -> bool:
    summary = _summarize_round(results, target_classes)
    enrolled = bool(summary["enrolled"])
    texts_obj = summary["texts"]
    texts = texts_obj if isinstance(texts_obj, list) else []

    reporter.update(enrolled=enrolled, round_no=request_no)
    reporter.log(f"Step {request_no}: enrolled={'YES' if enrolled else 'NO'}")
    if texts:
        for text in texts:
            reporter.log(f"Server: {text}")

    if enrolled:
        reporter.update(
            status="success",
            message="Enrollment detected. Task stopped.",
            enrolled=True,
        )
        reporter.log("Status: enrollment detected, stopped")
        return True
    return False


def _sleep_until(next_start: float) -> float:
    sleep_seconds = next_start - time.monotonic()
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
        return next_start
    return time.monotonic()


def _run_smooth_strategy(
    page: Any,
    payload: Dict[str, Optional[str]],
    target_classes: List[int],
    settings: RushSettings,
    reporter: RunReporter,
) -> None:
    interval = 1.0 / settings.smooth_requests_per_second
    total = settings.smooth_total_requests
    reporter.log(
        f"Strategy: smooth, {settings.smooth_requests_per_second:.2f} requests/s, "
        f"total={total if total > 0 else 'infinite'}"
    )
    request_no = 1
    next_start = time.monotonic()
    while True:
        if total > 0 and request_no > total:
            reporter.update(status="completed", message="All configured requests finished.", round_no=request_no - 1)
            reporter.log("Status: completed configured requests")
            break

        reporter.update(status="running", round_no=request_no, message="Replaying requests.")
        reporter.log(f"Request {request_no}/{total if total > 0 else 'infinite'}: sending 1 request")
        results = _send_replay_requests(page, payload, 1)
        if _handle_replay_results(results, target_classes, request_no, reporter):
            break

        request_no += 1
        next_start += interval
        next_start = _sleep_until(next_start)


def _run_burst_strategy(
    page: Any,
    payload: Dict[str, Optional[str]],
    target_classes: List[int],
    settings: RushSettings,
    reporter: RunReporter,
) -> None:
    interval = 1.0 / settings.burst_rounds_per_second
    total = settings.burst_rounds
    reporter.log(
        f"Strategy: burst, {settings.burst_rounds_per_second:.2f} rounds/s, "
        f"{settings.burst_count} requests/round, total={total if total > 0 else 'infinite'} rounds"
    )
    round_no = 1
    next_start = time.monotonic()
    while True:
        if total > 0 and round_no > total:
            reporter.update(status="completed", message="All configured burst rounds finished.", round_no=round_no - 1)
            reporter.log("Status: completed configured burst rounds")
            break

        reporter.update(status="running", round_no=round_no, message="Replaying requests.")
        reporter.log(f"Burst {round_no}/{total if total > 0 else 'infinite'}: sending {settings.burst_count} requests")
        results = _send_replay_requests(page, payload, settings.burst_count)
        if _handle_replay_results(results, target_classes, round_no, reporter):
            break

        round_no += 1
        next_start += interval
        next_start = _sleep_until(next_start)


def _run_hybrid_strategy(
    page: Any,
    payload: Dict[str, Optional[str]],
    target_classes: List[int],
    settings: RushSettings,
    reporter: RunReporter,
) -> None:
    total = settings.hybrid_total_requests
    sent = 0
    step_no = 1
    reporter.log(
        "Strategy: hybrid, "
        f"{settings.hybrid_burst_rounds} burst rounds x {settings.hybrid_burst_count} requests "
        f"at {settings.hybrid_burst_rounds_per_second:.2f} rounds/s, then "
        f"{settings.hybrid_smooth_requests_per_second:.2f} requests/s smooth, "
        f"total={total if total > 0 else 'infinite'} requests"
    )

    burst_interval = 1.0 / settings.hybrid_burst_rounds_per_second
    next_start = time.monotonic()
    for burst_no in range(1, settings.hybrid_burst_rounds + 1):
        if total > 0 and sent >= total:
            break
        request_count = settings.hybrid_burst_count
        if total > 0:
            request_count = min(request_count, total - sent)
        reporter.update(status="running", round_no=step_no, message="Replaying burst requests.")
        reporter.log(f"Hybrid burst {burst_no}/{settings.hybrid_burst_rounds}: sending {request_count} requests")
        results = _send_replay_requests(page, payload, request_count)
        sent += request_count
        if _handle_replay_results(results, target_classes, step_no, reporter):
            return
        step_no += 1
        next_start += burst_interval
        next_start = _sleep_until(next_start)

    smooth_interval = 1.0 / settings.hybrid_smooth_requests_per_second
    next_start = time.monotonic()
    while True:
        if total > 0 and sent >= total:
            reporter.update(status="completed", message="All configured hybrid requests finished.", round_no=step_no - 1)
            reporter.log("Status: completed configured hybrid requests")
            break

        reporter.update(status="running", round_no=step_no, message="Replaying smooth requests.")
        reporter.log(f"Hybrid smooth request {sent + 1}/{total if total > 0 else 'infinite'}")
        results = _send_replay_requests(page, payload, 1)
        sent += 1
        if _handle_replay_results(results, target_classes, step_no, reporter):
            break

        step_no += 1
        next_start += smooth_interval
        next_start = _sleep_until(next_start)


def _click_enroll_once(page: Any) -> str:
    script = r"""
    () => {
      const elements = Array.from(document.querySelectorAll(
        'button, a, input[type="button"], input[type="submit"], [role="button"]'
      ));
      const textOf = (el) => (
        el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.title || ''
      ).replace(/\s+/g, ' ').trim();
      const candidates = elements
        .map((el) => ({ el, text: textOf(el) }))
        .filter((item) => item.text && !item.el.disabled && item.el.getAttribute('aria-disabled') !== 'true');

      const exact = candidates.find((item) => /^Enroll In Selected Classes$/i.test(item.text));
      const selected = candidates.find((item) => /Enroll/i.test(item.text) && /Selected Classes/i.test(item.text));
      const target = exact || selected;
      if (!target) return '';
      target.el.click();
      return target.text;
    }
    """
    for frame in page.frames:
        try:
            clicked_text = frame.evaluate(script)
        except Exception:
            continue
        if clicked_text:
            return str(clicked_text)
    return ""


def _log_speed_settings(settings: RushSettings, reporter: RunReporter) -> None:
    effective_rps = _effective_requests_per_second(settings)
    if effective_rps is None:
        reporter.log("Speed: unpaced")
    else:
        reporter.log(f"Speed: {effective_rps:.2f} requests/s effective")
    if settings.rate_limit_override_enabled:
        reporter.log(f"Safety cap: override verified, {settings.rate_limit_cap_per_second:.0f} requests/s")
    else:
        reporter.log(f"Safety cap: {settings.rate_limit_cap_per_second:.0f} requests/s")
    if settings.rate_limit_capped:
        reporter.log("Safety cap adjusted the requested speed")


def run_capture_and_replay(settings: RushSettings, reporter: RunReporter) -> None:
    try:
        from playwright.sync_api import Request, sync_playwright
    except Exception as exc:
        reporter.update(status="failed", message="Playwright is not installed or cannot load.")
        reporter.log("Failed to import Playwright.")
        reporter.log("Install dependencies with: python -m pip install -r requirements.txt")
        reporter.log(f"Details: {exc}")
        return

    captured: List[CapturedRequest] = []
    capture_enabled = True
    keywords = settings.capture_keywords or ["IScript_Enroll"]

    reporter.update(status="starting", message="Connecting to Edge CDP.")
    reporter.log("Status: connecting to browser")

    configured_targets = _configured_class_numbers(settings)
    if configured_targets:
        reporter.log(f"Cart classes: {configured_targets}")
    _log_speed_settings(settings, reporter)

    def on_request(req: Request) -> None:
        nonlocal capture_enabled
        if not capture_enabled:
            return
        if not any(keyword in req.url for keyword in keywords):
            return
        captured.append(
            CapturedRequest(
                url=req.url,
                method=req.method,
                headers=_normalize_headers(req.headers),
                body=req.post_data,
                timestamp=time.time(),
            )
        )
        reporter.update(message=f"Captured candidate request: {_endpoint_name(req.url)}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(settings.cdp_url)
        except Exception as exc:
            reporter.update(status="failed", message="Failed to connect Edge by CDP.")
            reporter.log("Status: failed to connect browser")
            reporter.log(f"Reason: {exc}")
            return

        context, page = _select_page(browser, settings.page_url_keyword)
        if page is None or context is None:
            reporter.update(status="failed", message="No open Edge tabs found.")
            reporter.log("Status: no matching browser tab")
            browser.close()
            return

        context.on("request", on_request)
        reporter.update(
            status="capturing",
            message="Waiting for manual enroll click.",
            attached_url=page.url,
        )
        reporter.log("Status: browser attached")
        if settings.auto_click_enroll:
            reporter.log("Action: auto-clicking Enroll once")
            clicked_text = _click_enroll_once(page)
            if clicked_text:
                reporter.log(f"Status: clicked {clicked_text}")
            else:
                reporter.log("Action needed: click Enroll once in Edge")
        else:
            reporter.log("Action needed: click Enroll once in Edge")

        started = time.time()
        while not captured and (time.time() - started) < settings.capture_timeout:
            page.wait_for_timeout(200)

        if not captured:
            reporter.update(status="failed", message="Timed out without matching request.")
            reporter.log("Status: capture timed out")
            browser.close()
            return

        settle_start = time.time()
        last_seen_count = len(captured)
        last_seen_change = time.time()
        while (time.time() - settle_start) < settings.capture_settle_seconds:
            page.wait_for_timeout(150)
            if len(captured) != last_seen_count:
                last_seen_count = len(captured)
                last_seen_change = time.time()
            if (time.time() - last_seen_change) >= settings.capture_settle_seconds:
                break

        latest = _choose_replay_request(captured)
        payload = {
            "url": latest.url,
            "method": latest.method,
            "headers": latest.headers,
            "body": latest.body,
        }

        body_targets = _extract_target_classes_from_body(latest.body)
        target_classes = body_targets or configured_targets
        reporter.update(
            status="running",
            message="Captured request template. Replaying now.",
            captured_url=latest.url,
            target_classes=target_classes,
        )
        reporter.log(f"Status: captured {_endpoint_name(latest.url)} ({len(captured)} matched)")
        if body_targets:
            reporter.log(f"Target classes: {body_targets}")
        elif configured_targets:
            reporter.log(f"Target classes: {configured_targets}")
        else:
            reporter.log("Target classes: unknown")

        capture_enabled = False

        if settings.strategy_mode == "burst":
            _run_burst_strategy(page, payload, target_classes, settings, reporter)
        elif settings.strategy_mode == "hybrid":
            _run_hybrid_strategy(page, payload, target_classes, settings, reporter)
        else:
            _run_smooth_strategy(page, payload, target_classes, settings, reporter)

        browser.close()
