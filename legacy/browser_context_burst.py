import argparse
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from playwright.sync_api import Browser, Request, sync_playwright


DEFAULT_CAPTURE_KEYWORDS = ["IScript_Enroll"]
DEFAULT_BURST_COUNT = 20
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_SETTLE_SECONDS = 1.5
DEFAULT_BURSTS_PER_SECOND = 0.0


@dataclass
class CapturedRequest:
    # Full target URL including query params.
    url: str
    # HTTP method (POST/GET/...).
    method: str
    # Request headers used during replay.
    headers: Dict[str, str]
    # Request body as raw string if present.
    body: Optional[str]
    # Capture timestamp for debug logs.
    timestamp: float


def _normalize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Remove headers that should be controlled by the browser networking stack.
    Keeping these can cause protocol errors during replay.
    """
    blocked = {
        "cookie",
        "host",
        "content-length",
        "connection",
        "origin",
    }
    normalized: Dict[str, str] = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in blocked:
            continue
        normalized[key_lower] = value
    return normalized


def _extract_texts_from_payload(payload: object) -> List[str]:
    """
    Extract user-facing message texts from known response fields.
    """
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
    """
    Build {classNbr: isEnrolled} from classResponses.
    """
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
    """
    Parse target class numbers from enroll request body:
    {"sections":[{"classNbr":1041}, ...], ...}
    """
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
    """
    Stop condition:
    - if target classes are known: ALL target classes must be enrolled.
    - if unknown: all returned classResponses must be enrolled (conservative fallback).
    """
    enrolled_map = _extract_enrolled_map(payload)
    if not enrolled_map:
        return False

    if target_classes:
        for class_nbr in target_classes:
            if not enrolled_map.get(class_nbr, False):
                return False
        return True

    return all(enrolled_map.values())


def _summarize_round(results: List[Dict[str, object]], target_classes: List[int]) -> Dict[str, object]:
    enrolled = False
    texts: List[str] = []

    for item in results:
        if not item.get("ok"):
            continue
        payload = item.get("response")
        if _payload_enrolled_for_targets(payload, target_classes):
            enrolled = True
        texts.extend(_extract_texts_from_payload(payload))

    # De-duplicate while keeping original order.
    seen = set()
    unique_texts: List[str] = []
    for text in texts:
        if text in seen:
            continue
        seen.add(text)
        unique_texts.append(text)

    return {"enrolled": enrolled, "texts": unique_texts}


def _choose_replay_request(captured: List[CapturedRequest]) -> CapturedRequest:
    """
    One enroll click may trigger multiple API calls.
    We prioritize the true enroll endpoint over helper/status endpoints.
    """
    for item in reversed(captured):
        if "IScript_Enroll" in item.url:
            return item
    for item in reversed(captured):
        if "IScript_SaveSelections" in item.url:
            return item
    return captured[-1]


def _select_page(browser: Browser, page_url_keyword: str):
    """
    Pick one page from already-open Edge tabs.
    Priority:
    1) URL contains page_url_keyword
    2) first non-empty URL
    3) first tab if everything is blank
    """
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Attach to an already-open Edge browser, capture the enroll request after your manual click, "
            "then replay it in burst mode."
        )
    )
    parser.add_argument(
        "--cdp-url",
        default="http://127.0.0.1:9222",
        help="Edge remote-debugging CDP endpoint.",
    )
    parser.add_argument(
        "--page-url-keyword",
        default="dkuhub.dku.edu.cn",
        help="Use this keyword to choose which already-open tab to bind.",
    )
    parser.add_argument(
        "--capture-keywords",
        default=",".join(DEFAULT_CAPTURE_KEYWORDS),
        help="Comma-separated substrings used to match target request URLs.",
    )
    parser.add_argument(
        "--capture-timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Max seconds to wait for your manual click request.",
    )
    parser.add_argument(
        "--capture-settle-seconds",
        type=float,
        default=DEFAULT_SETTLE_SECONDS,
        help=(
            "After first matched request, keep listening this long to collect the whole "
            "request burst from one click."
        ),
    )
    parser.add_argument(
        "--burst-count",
        type=int,
        default=DEFAULT_BURST_COUNT,
        help="How many requests to fire per round.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=0,
        help="How many replay rounds to run. Use 0 for infinite loop.",
    )
    parser.add_argument(
        "--round-interval",
        type=float,
        default=0.0,
        help="Delay between rounds (seconds).",
    )
    parser.add_argument(
        "--bursts-per-second",
        type=float,
        default=DEFAULT_BURSTS_PER_SECOND,
        help=(
            "Target burst rounds per second. "
            "If > 0, program will pace rounds to approximately this rate."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keywords = [x.strip() for x in args.capture_keywords.split(",") if x.strip()]
    captured: List[CapturedRequest] = []
    capture_enabled = True

    def on_request(req: Request) -> None:
        # Capture only requests that match configured URL keywords.
        if not capture_enabled:
            return
        if not any(k in req.url for k in keywords):
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
        print(f"[capture] {req.method} {req.url}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(args.cdp_url)
        except Exception as exc:
            print("Failed to connect Edge by CDP.")
            print(f"CDP endpoint: {args.cdp_url}")
            print("Start Edge with remote debugging enabled, for example:")
            print(
                'msedge.exe --remote-debugging-port=9222 --user-data-dir="D:\\\\edge-cdp-profile"'
            )
            print(f"Details: {exc}")
            return

        context, page = _select_page(browser, args.page_url_keyword)
        if page is None or context is None:
            print("No open Edge tabs found. Open the course page in Edge first, then rerun.")
            browser.close()
            return

        # Listen at context level to avoid missing iframe/subframe requests.
        context.on("request", on_request)

        print(f"Attached tab: {page.url}")
        print("Now click the enroll button in Edge. Waiting for matching request...")

        started = time.time()
        while not captured and (time.time() - started) < args.capture_timeout:
            # Sleep by driving the browser event loop to receive request events.
            page.wait_for_timeout(200)

        if not captured:
            print("Timed out without matching request.")
            print("Tips:")
            print("1) confirm capture keyword (default: IScript_Enroll)")
            print("2) confirm you clicked enroll after this script started")
            print("3) confirm the tab belongs to the same Edge CDP session")
            browser.close()
            return

        # After first match, wait a short settle window to collect the full
        # sequence triggered by a single click (e.g. SaveSelections + Enroll).
        settle_start = time.time()
        last_seen_count = len(captured)
        last_seen_change = time.time()
        while (time.time() - settle_start) < args.capture_settle_seconds:
            page.wait_for_timeout(150)
            if len(captured) != last_seen_count:
                last_seen_count = len(captured)
                last_seen_change = time.time()
            if (time.time() - last_seen_change) >= args.capture_settle_seconds:
                break

        # Pick the most meaningful request for replay.
        latest = _choose_replay_request(captured)
        print("Captured request template:")
        print(f"  METHOD: {latest.method}")
        print(f"  URL: {latest.url}")
        print(f"  CANDIDATES SEEN: {len(captured)}")

        payload = {
            "url": latest.url,
            "method": latest.method,
            "headers": latest.headers,
            "body": latest.body,
        }
        target_classes = _extract_target_classes_from_body(latest.body)
        if target_classes:
            print(f"  TARGET CLASSES: {target_classes}")
        else:
            print("  TARGET CLASSES: (unknown, fallback to all classResponses enrolled)")

        # Stop capturing before replay to avoid logging our own replay traffic.
        capture_enabled = False

        if args.bursts_per_second < 0:
            print("Invalid value: --bursts-per-second must be >= 0.")
            browser.close()
            return
        if args.rounds < 0:
            print("Invalid value: --rounds must be >= 0.")
            browser.close()
            return

        pacing_interval = 0.0
        if args.bursts_per_second > 0:
            pacing_interval = 1.0 / args.bursts_per_second
            print(
                f"Replay pace: {args.bursts_per_second:.3f} burst/s "
                f"(target interval {pacing_interval:.3f}s)"
            )
        elif args.round_interval > 0:
            pacing_interval = args.round_interval
            print(f"Replay pace: fixed interval {pacing_interval:.3f}s between rounds")
        else:
            print("Replay pace: no delay (next round starts immediately)")

        round_no = 1
        next_round_start = time.monotonic()
        while True:
            if args.rounds > 0 and round_no > args.rounds:
                break

            print(f"[round {round_no}] replaying {args.burst_count} requests...")
            results = page.evaluate(
                """
                async ({req, burstCount}) => {
                    const jobs = [];
                    for (let i = 0; i < burstCount; i += 1) {
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
                {"req": payload, "burstCount": args.burst_count},
            )

            summary = _summarize_round(results, target_classes)
            enrolled = bool(summary["enrolled"])
            texts_obj = summary["texts"]
            texts = texts_obj if isinstance(texts_obj, list) else []

            print(f"[round {round_no}] enrolled={'YES' if enrolled else 'NO'}")
            if texts:
                for text in texts:
                    print(f"text: {text}")
            else:
                print("text: (empty)")

            if enrolled:
                print("Enrollment detected. Stop now.")
                break

            round_no += 1
            if pacing_interval > 0:
                next_round_start += pacing_interval
                sleep_seconds = next_round_start - time.monotonic()
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                else:
                    # If one round took too long, resync schedule without extra sleep.
                    next_round_start = time.monotonic()

        browser.close()


if __name__ == "__main__":
    main()
