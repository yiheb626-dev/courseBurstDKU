from __future__ import annotations

import hashlib
import hmac
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


MAX_SAFE_REQUESTS_PER_SECOND = 5.0
MAX_VERIFIED_REQUESTS_PER_SECOND = 50.0
RATE_LIMIT_OVERRIDE_SALT_HEX = "6f4b1ad68ecbf5832e9c118a4bbd7229"
RATE_LIMIT_OVERRIDE_HASH_HEX = "c79ae2aafd1859af37f92a06f695eb282abd10a59e1d2974beee0cb8e7fd8fb1"
RATE_LIMIT_OVERRIDE_ITERATIONS = 260_000
DEFAULT_TIME_SERVER = "ntp.tencent.com"
STRATEGY_SMOOTH = "smooth"
STRATEGY_BURST = "burst"
STRATEGY_HYBRID = "hybrid"
STRATEGY_MODES = {STRATEGY_SMOOTH, STRATEGY_BURST, STRATEGY_HYBRID}
DEFAULT_BURST_COUNT = 5
DEFAULT_BURST_ROUNDS_PER_SECOND = 0.9
DEFAULT_BURST_ROUNDS = 10


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CourseSelection:
    name: str = ""
    class_nbr: Optional[int] = None
    component: str = ""
    section: str = ""
    instructor: str = ""
    note: str = ""

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "CourseSelection":
        class_nbr = raw.get("class_nbr")
        if class_nbr in ("", None):
            parsed_class_nbr = None
        else:
            try:
                parsed_class_nbr = int(class_nbr)
            except (TypeError, ValueError):
                parsed_class_nbr = None
        return cls(
            name=str(raw.get("name", "")).strip(),
            class_nbr=parsed_class_nbr,
            component=str(raw.get("component", "")).strip().upper(),
            section=str(raw.get("section", "")).strip(),
            instructor=str(raw.get("instructor", "")).strip(),
            note=str(raw.get("note", "")).strip(),
        )


@dataclass
class RushSettings:
    cdp_url: str = "http://127.0.0.1:9222"
    page_url_keyword: str = "dkuhub.dku.edu.cn"
    capture_keywords: List[str] = field(default_factory=lambda: ["IScript_Enroll"])
    capture_timeout: int = 120
    capture_settle_seconds: float = 1.5
    burst_count: int = 5
    rounds: int = 10
    round_interval: float = 2.0
    bursts_per_second: float = 0.5
    strategy_mode: str = STRATEGY_SMOOTH
    strategy_error: str = ""
    smooth_requests_per_second: float = 2.5
    smooth_total_requests: int = 50
    burst_rounds_per_second: float = 0.9
    burst_rounds: int = 10
    hybrid_burst_count: int = 5
    hybrid_burst_rounds: int = 2
    hybrid_burst_rounds_per_second: float = 0.9
    hybrid_smooth_requests_per_second: float = 2.5
    hybrid_total_requests: int = 50
    auto_click_enroll: bool = True
    keep_session_alive: bool = True
    rate_limit_override_code: str = ""
    rate_limit_override_enabled: bool = False
    rate_limit_cap_per_second: float = MAX_SAFE_REQUESTS_PER_SECOND
    rate_limit_capped: bool = False
    time_sync_enabled: bool = True
    time_sync_server: str = DEFAULT_TIME_SERVER
    time_offset_ms: Optional[float] = None
    time_sync_rtt_ms: Optional[float] = None
    time_sync_checked_at: str = ""
    time_sync_error: str = ""
    scheduled_start: Optional[str] = None
    selected_courses: List[CourseSelection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any], trust_persisted_override: bool = False) -> "RushSettings":
        keywords_raw = raw.get("capture_keywords", ["IScript_Enroll"])
        if isinstance(keywords_raw, str):
            keywords = [item.strip() for item in keywords_raw.split(",") if item.strip()]
        elif isinstance(keywords_raw, list):
            keywords = [str(item).strip() for item in keywords_raw if str(item).strip()]
        else:
            keywords = ["IScript_Enroll"]

        courses_raw = raw.get("selected_courses", [])
        courses = []
        if isinstance(courses_raw, list):
            courses = [
                CourseSelection.from_dict(item)
                for item in courses_raw
                if isinstance(item, dict)
            ]

        strategy_mode = str(raw.get("strategy_mode", STRATEGY_SMOOTH)).strip().lower()
        if strategy_mode not in STRATEGY_MODES:
            strategy_mode = STRATEGY_SMOOTH

        override_code = str(raw.get("rate_limit_override_code", "")).strip()
        persisted_override = (
            _parse_bool(raw.get("rate_limit_override_enabled", False))
            if trust_persisted_override
            else False
        )
        override_enabled = persisted_override or is_rate_limit_override_valid(override_code)
        rate_limit_cap = (
            MAX_VERIFIED_REQUESTS_PER_SECOND
            if override_enabled
            else MAX_SAFE_REQUESTS_PER_SECOND
        )
        rate_limit_capped = False
        strategy_error = ""

        burst_count = _parse_int(raw.get("burst_count"), DEFAULT_BURST_COUNT, minimum=1)
        rounds = _parse_int(raw.get("rounds"), 10, minimum=0)
        round_interval = _parse_float(raw.get("round_interval"), 2.0, minimum=0.0)
        bursts_per_second = _parse_float(raw.get("bursts_per_second"), 0.5, minimum=0.0)

        smooth_requests_per_second = _parse_float(
            raw.get("smooth_requests_per_second"), 2.5, minimum=0.1
        )
        smooth_total_requests = _parse_int(raw.get("smooth_total_requests"), 50, minimum=0)
        burst_rounds_per_second = _parse_float(
            raw.get("burst_rounds_per_second", raw.get("bursts_per_second")),
            DEFAULT_BURST_ROUNDS_PER_SECOND,
            minimum=0.1,
        )
        burst_rounds = _parse_int(
            raw.get("burst_rounds", raw.get("rounds")),
            DEFAULT_BURST_ROUNDS,
            minimum=0,
        )
        hybrid_burst_count = _parse_int(raw.get("hybrid_burst_count"), 5, minimum=1)
        hybrid_burst_rounds = _parse_int(raw.get("hybrid_burst_rounds"), 2, minimum=0)
        hybrid_burst_rounds_per_second = _parse_float(
            raw.get("hybrid_burst_rounds_per_second"), 0.9, minimum=0.1
        )
        hybrid_smooth_requests_per_second = _parse_float(
            raw.get("hybrid_smooth_requests_per_second"), 2.5, minimum=0.1
        )
        hybrid_total_requests = _parse_int(raw.get("hybrid_total_requests"), 50, minimum=0)

        if strategy_mode == STRATEGY_HYBRID and not override_enabled:
            strategy_error = "混合策略需要先验证 override code。"
        elif (
            strategy_mode == STRATEGY_BURST
            and not override_enabled
            and not _is_default_burst_config(
                burst_count,
                burst_rounds_per_second,
                burst_rounds,
            )
        ):
            strategy_error = "burst 未验证时只能使用默认参数。"

        if smooth_requests_per_second > rate_limit_cap:
            smooth_requests_per_second = rate_limit_cap
            rate_limit_capped = True

        max_burst_rounds_per_second = rate_limit_cap / burst_count
        if burst_rounds_per_second * burst_count > rate_limit_cap:
            burst_rounds_per_second = max_burst_rounds_per_second
            rate_limit_capped = True
        bursts_per_second = burst_rounds_per_second
        rounds = burst_rounds
        round_interval = 1.0 / burst_rounds_per_second if burst_rounds_per_second > 0 else 0.0

        max_hybrid_burst_rounds_per_second = rate_limit_cap / hybrid_burst_count
        if hybrid_burst_rounds_per_second * hybrid_burst_count > rate_limit_cap:
            hybrid_burst_rounds_per_second = max_hybrid_burst_rounds_per_second
            rate_limit_capped = True
        if hybrid_smooth_requests_per_second > rate_limit_cap:
            hybrid_smooth_requests_per_second = rate_limit_cap
            rate_limit_capped = True

        return cls(
            cdp_url=str(raw.get("cdp_url", cls.cdp_url)).strip()
            or "http://127.0.0.1:9222",
            page_url_keyword=str(raw.get("page_url_keyword", cls.page_url_keyword)).strip(),
            capture_keywords=keywords or ["IScript_Enroll"],
            capture_timeout=max(1, int(float(raw.get("capture_timeout", 120)))),
            capture_settle_seconds=max(
                0.1, float(raw.get("capture_settle_seconds", 1.5))
            ),
            burst_count=burst_count,
            rounds=rounds,
            round_interval=round_interval,
            bursts_per_second=bursts_per_second,
            strategy_mode=strategy_mode,
            strategy_error=strategy_error,
            smooth_requests_per_second=smooth_requests_per_second,
            smooth_total_requests=smooth_total_requests,
            burst_rounds_per_second=burst_rounds_per_second,
            burst_rounds=burst_rounds,
            hybrid_burst_count=hybrid_burst_count,
            hybrid_burst_rounds=hybrid_burst_rounds,
            hybrid_burst_rounds_per_second=hybrid_burst_rounds_per_second,
            hybrid_smooth_requests_per_second=hybrid_smooth_requests_per_second,
            hybrid_total_requests=hybrid_total_requests,
            auto_click_enroll=_parse_bool(raw.get("auto_click_enroll", True)),
            keep_session_alive=_parse_bool(raw.get("keep_session_alive", True)),
            rate_limit_override_code="",
            rate_limit_override_enabled=override_enabled,
            rate_limit_cap_per_second=rate_limit_cap,
            rate_limit_capped=rate_limit_capped,
            time_sync_enabled=_parse_bool(raw.get("time_sync_enabled", True)),
            time_sync_server=str(raw.get("time_sync_server", DEFAULT_TIME_SERVER)).strip()
            or DEFAULT_TIME_SERVER,
            time_offset_ms=_parse_optional_float(raw.get("time_offset_ms")),
            time_sync_rtt_ms=_parse_optional_float(raw.get("time_sync_rtt_ms")),
            time_sync_checked_at=str(raw.get("time_sync_checked_at") or "").strip(),
            time_sync_error=str(raw.get("time_sync_error") or "").strip(),
            scheduled_start=str(raw.get("scheduled_start") or "").strip() or None,
            selected_courses=courses,
        )


@dataclass
class JobConfig:
    job_id: str
    created_at: str
    settings: RushSettings

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "JobConfig":
        return cls(
            job_id=str(raw["job_id"]),
            created_at=str(raw.get("created_at") or utc_now_iso()),
            settings=RushSettings.from_dict(
                raw.get("settings", {}),
                trust_persisted_override=True,
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "y"}
    return bool(value)


def _parse_float(value: object, default: float, minimum: float = 0.0) -> float:
    if value in ("", None):
        parsed = default
    else:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = default
    return max(minimum, parsed)


def _parse_int(value: object, default: int, minimum: int = 0) -> int:
    if value in ("", None):
        parsed = default
    else:
        try:
            parsed = int(float(value))
        except (TypeError, ValueError):
            parsed = default
    return max(minimum, parsed)


def _is_default_burst_config(
    burst_count: int,
    burst_rounds_per_second: float,
    burst_rounds: int,
) -> bool:
    return (
        burst_count == DEFAULT_BURST_COUNT
        and abs(burst_rounds_per_second - DEFAULT_BURST_ROUNDS_PER_SECOND) < 1e-9
        and burst_rounds == DEFAULT_BURST_ROUNDS
    )


def _parse_optional_float(value: object) -> Optional[float]:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_rate_limit_override_valid(code: str) -> bool:
    if not code:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        code.encode("utf-8"),
        bytes.fromhex(RATE_LIMIT_OVERRIDE_SALT_HEX),
        RATE_LIMIT_OVERRIDE_ITERATIONS,
    )
    return hmac.compare_digest(digest.hex(), RATE_LIMIT_OVERRIDE_HASH_HEX)


@dataclass
class JobStatus:
    job_id: str
    status: str = "created"
    message: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    pid: Optional[int] = None
    attached_url: str = ""
    captured_url: str = ""
    target_classes: List[int] = field(default_factory=list)
    round_no: int = 0
    enrolled: bool = False
    selected_courses: List[CourseSelection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "JobStatus":
        courses_raw = raw.get("selected_courses", [])
        courses = [
            CourseSelection.from_dict(item)
            for item in courses_raw
            if isinstance(item, dict)
        ] if isinstance(courses_raw, list) else []
        return cls(
            job_id=str(raw.get("job_id", "")),
            status=str(raw.get("status", "created")),
            message=str(raw.get("message", "")),
            created_at=str(raw.get("created_at") or utc_now_iso()),
            updated_at=str(raw.get("updated_at") or utc_now_iso()),
            started_at=raw.get("started_at"),
            finished_at=raw.get("finished_at"),
            pid=raw.get("pid"),
            attached_url=str(raw.get("attached_url", "")),
            captured_url=str(raw.get("captured_url", "")),
            target_classes=[int(item) for item in raw.get("target_classes", [])],
            round_no=int(raw.get("round_no", 0) or 0),
            enrolled=bool(raw.get("enrolled", False)),
            selected_courses=courses,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
