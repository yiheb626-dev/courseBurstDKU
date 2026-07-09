from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .core.burst_engine import run_capture_and_replay
from .core.models import JobConfig, JobStatus, utc_now_iso


class FileReporter:
    def __init__(self, job_config: JobConfig, status_path: Path, log_path: Path) -> None:
        self.job_config = job_config
        self.status_path = status_path
        self.log_path = log_path
        self.status = JobStatus(
            job_id=job_config.job_id,
            status="starting",
            message="Task process started.",
            created_at=job_config.created_at,
            started_at=utc_now_iso(),
            pid=os.getpid(),
            selected_courses=job_config.settings.selected_courses,
        )
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_status()

    def log(self, message: str) -> None:
        line = f"{utc_now_iso()} {message}"
        print(message, flush=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def update(self, **fields: Any) -> None:
        for key, value in fields.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)
        self.status.updated_at = utc_now_iso()
        if self.status.status in {"success", "completed", "failed", "stopped"}:
            self.status.finished_at = self.status.finished_at or utc_now_iso()
        self._write_status()

    def _write_status(self) -> None:
        payload: Dict[str, Any] = asdict(self.status)
        tmp_path = self.status_path.with_suffix(self.status_path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.status_path)


def _load_config(path: Path) -> JobConfig:
    return JobConfig.from_dict(json.loads(path.read_text(encoding="utf-8-sig")))


def _log_time_sync(config: JobConfig, reporter: FileReporter) -> None:
    settings = config.settings
    if not settings.time_sync_enabled:
        reporter.log("Time sync: disabled")
    elif settings.time_offset_ms is None:
        reporter.log(f"Time sync: failed; using local clock. {settings.time_sync_error}")
    else:
        reporter.log(
            f"Time sync: {settings.time_sync_server}, "
            f"offset={settings.time_offset_ms:+.1f} ms, "
            f"RTT={settings.time_sync_rtt_ms or 0:.1f} ms"
        )
    if settings.scheduled_start:
        reporter.log(
            "Timing: launch = scheduled start "
            f"- capture settle {settings.capture_settle_seconds:.1f}s "
            f"- NTP offset {(settings.time_offset_ms or 0.0):+.1f}ms"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a configured course rush job.")
    parser.add_argument("--config", required=True, help="Path to job config JSON.")
    parser.add_argument("--status", required=True, help="Path to status JSON.")
    parser.add_argument("--log", required=True, help="Path to log file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = _load_config(Path(args.config))
    reporter = FileReporter(config, Path(args.status), Path(args.log))
    reporter.log(f"Job: {config.job_id}")
    _log_time_sync(config, reporter)
    reporter.log("Cart courses:")
    if config.settings.selected_courses:
        for course in config.settings.selected_courses:
            reporter.log(
                f"  - {course.name or '(unnamed)'} "
                f"{course.component or '-'} "
                f"class={course.class_nbr or '-'} section={course.section or '-'}"
            )
    else:
        reporter.log("  (none; captured request decides target)")

    try:
        run_capture_and_replay(config.settings, reporter)
    except KeyboardInterrupt:
        reporter.update(status="stopped", message="Stopped by user.")
        reporter.log("Stopped by user.")
        return 130
    except Exception as exc:
        reporter.update(status="failed", message=str(exc))
        reporter.log(f"Unhandled error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
