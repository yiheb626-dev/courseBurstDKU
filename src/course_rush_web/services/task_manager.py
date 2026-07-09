from __future__ import annotations

import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.models import JobConfig, JobStatus, RushSettings, utc_now_iso
from .job_store import JobStore
from .time_sync import TimeSyncClient


SESSION_REFRESH_SECONDS = 600


class TaskManager:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.src_root = project_root / "src"
        self.store = JobStore(project_root)
        self.time_sync = TimeSyncClient()
        self._lock = threading.Lock()
        self._timers: Dict[str, threading.Timer] = {}
        self._refresh_timers: Dict[str, threading.Timer] = {}
        self._processes: Dict[str, subprocess.Popen[Any]] = {}

    def create_job(self, raw_settings: Dict[str, Any]) -> Dict[str, Any]:
        settings = RushSettings.from_dict(raw_settings)
        if settings.strategy_error:
            return {
                "error": "strategy_locked",
                "message": settings.strategy_error,
                "status": "rejected",
            }
        if settings.time_sync_enabled:
            self._apply_time_sync(settings)

        job_id = self._new_job_id()
        config = JobConfig(job_id=job_id, created_at=utc_now_iso(), settings=settings)
        self.store.save_config(config)

        timing_note = self._timing_note(settings)
        status = JobStatus(
            job_id=job_id,
            status="created",
            message=f"Job created. {timing_note}".strip(),
            created_at=config.created_at,
            selected_courses=settings.selected_courses,
        )
        self.store.save_status(status)

        delay = self._delay_until(settings)
        if delay > 0:
            status.status = "scheduled"
            status.message = f"Scheduled to start at {settings.scheduled_start}. {timing_note}".strip()
            status.updated_at = utc_now_iso()
            self.store.save_status(status)
            timer = threading.Timer(delay, self._launch_job, args=(job_id,))
            timer.daemon = True
            with self._lock:
                self._timers[job_id] = timer
            timer.start()
            if settings.keep_session_alive:
                self._schedule_session_refresh(job_id)
        else:
            self._launch_job(job_id)

        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        status = self.store.load_status(job_id)
        config = self.store.load_config(job_id)
        if status is None:
            return {"error": "not_found"}
        payload = status.to_dict()
        payload["log"] = self.store.read_log_tail(job_id)
        if config is not None:
            payload["config"] = config.to_dict()
        return payload

    def list_jobs(self) -> Dict[str, Any]:
        return {"jobs": self.store.list_statuses()}

    def clear_history(self) -> Dict[str, Any]:
        with self._lock:
            timers = list(self._timers.values())
            refresh_timers = list(self._refresh_timers.values())
            processes = list(self._processes.values())
            self._timers.clear()
            self._refresh_timers.clear()
            self._processes.clear()

        for timer in timers + refresh_timers:
            timer.cancel()

        stopped_processes = 0
        for process in processes:
            if process.poll() is None:
                self._terminate_process_tree(process)
                stopped_processes += 1

        result = self.store.clear_history()
        result["stopped_processes"] = stopped_processes
        result["cancelled_timers"] = len(timers)
        result["cancelled_refresh_timers"] = len(refresh_timers)
        return result

    def stop_job(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            timer = self._timers.pop(job_id, None)
            refresh_timer = self._refresh_timers.pop(job_id, None)
            process = self._processes.pop(job_id, None)

        if timer is not None:
            timer.cancel()
        if refresh_timer is not None:
            refresh_timer.cancel()

        if process is not None and process.poll() is None:
            self._terminate_process_tree(process)

        status = self.store.load_status(job_id)
        if status is not None and status.status not in {"success", "completed", "failed"}:
            status.status = "stopped"
            status.message = "Stopped from web dashboard."
            status.updated_at = utc_now_iso()
            status.finished_at = status.finished_at or utc_now_iso()
            self.store.save_status(status)

        return self.get_job(job_id)

    def _launch_job(self, job_id: str) -> None:
        config = self.store.load_config(job_id)
        if config is None:
            return

        with self._lock:
            refresh_timer = self._refresh_timers.pop(job_id, None)
        if refresh_timer is not None:
            refresh_timer.cancel()

        status = self.store.load_status(job_id) or JobStatus(job_id=job_id)
        status.status = "starting"
        status.message = "Launching CLI window."
        status.updated_at = utc_now_iso()
        status.selected_courses = config.settings.selected_courses
        self.store.save_status(status)

        command = self._build_command(job_id)
        try:
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
                process = subprocess.Popen(command, creationflags=creationflags)
            else:
                process = subprocess.Popen(command)
        except Exception as exc:
            status.status = "failed"
            status.message = f"Failed to launch CLI: {exc}"
            status.updated_at = utc_now_iso()
            status.finished_at = utc_now_iso()
            self.store.save_status(status)
            return

        status.pid = process.pid
        status.message = "CLI window launched."
        status.updated_at = utc_now_iso()
        self.store.save_status(status)
        with self._lock:
            self._processes[job_id] = process
            self._timers.pop(job_id, None)

    def _build_command(self, job_id: str) -> list[str]:
        config_path = self.store.config_path(job_id)
        status_path = self.store.status_path(job_id)
        log_path = self.store.log_path(job_id)

        if os.name == "nt":
            if getattr(sys, "frozen", False):
                ps_command = (
                    f"Set-Location -LiteralPath {self._ps_quote(str(self.project_root))}; "
                    f"& {self._ps_quote(sys.executable)} --run-cli "
                    f"--config {self._ps_quote(str(config_path))} "
                    f"--status {self._ps_quote(str(status_path))} "
                    f"--log {self._ps_quote(str(log_path))}"
                )
            else:
                ps_command = (
                    f"$env:PYTHONPATH={self._ps_quote(str(self.src_root))}; "
                    f"Set-Location -LiteralPath {self._ps_quote(str(self.project_root))}; "
                    f"& {self._ps_quote(sys.executable)} -m course_rush_web.cli "
                    f"--config {self._ps_quote(str(config_path))} "
                    f"--status {self._ps_quote(str(status_path))} "
                    f"--log {self._ps_quote(str(log_path))}"
                )
            return [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_command,
            ]

        env_python = sys.executable
        if getattr(sys, "frozen", False):
            return [
                env_python,
                "--run-cli",
                "--config",
                str(config_path),
                "--status",
                str(status_path),
                "--log",
                str(log_path),
            ]
        return [
            env_python,
            "-m",
            "course_rush_web.cli",
            "--config",
            str(config_path),
            "--status",
            str(status_path),
            "--log",
            str(log_path),
        ]

    def _terminate_process_tree(self, process: subprocess.Popen[Any]) -> None:
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                pass
        process.terminate()

    def _schedule_session_refresh(self, job_id: str) -> None:
        config = self.store.load_config(job_id)
        if config is None:
            return
        delay = self._delay_until(config.settings)
        if delay <= SESSION_REFRESH_SECONDS:
            return

        timer = threading.Timer(SESSION_REFRESH_SECONDS, self._refresh_session, args=(job_id,))
        timer.daemon = True
        with self._lock:
            old_timer = self._refresh_timers.pop(job_id, None)
            self._refresh_timers[job_id] = timer
        if old_timer is not None:
            old_timer.cancel()
        timer.start()

    def _refresh_session(self, job_id: str) -> None:
        config = self.store.load_config(job_id)
        status = self.store.load_status(job_id)
        if config is None or status is None or status.status != "scheduled":
            return

        try:
            self._refresh_browser_page(config.settings)
            status.message = "Scheduled. Browser session refreshed."
        except Exception as exc:
            status.message = f"Scheduled. Session refresh failed: {exc}"
        status.updated_at = utc_now_iso()
        self.store.save_status(status)
        self._schedule_session_refresh(job_id)

    def _refresh_browser_page(self, settings: RushSettings) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(settings.cdp_url)
            pages = []
            for context in browser.contexts:
                pages.extend(context.pages)
            page = None
            if settings.page_url_keyword:
                for candidate in pages:
                    if settings.page_url_keyword in candidate.url:
                        page = candidate
                        break
            if page is None:
                page = next((candidate for candidate in pages if candidate.url and candidate.url != "about:blank"), None)
            if page is None:
                browser.close()
                raise RuntimeError("no browser tab found")
            page.reload(wait_until="domcontentloaded", timeout=15000)
            browser.close()

    def _apply_time_sync(self, settings: RushSettings) -> None:
        result = self.time_sync.measure(settings.time_sync_server)
        settings.time_sync_server = str(result.get("server_name") or settings.time_sync_server)
        settings.time_sync_checked_at = str(result.get("checked_at") or "")
        if result.get("ok"):
            settings.time_offset_ms = float(result["offset_ms"])
            settings.time_sync_rtt_ms = float(result["rtt_ms"])
            settings.time_sync_error = ""
        else:
            settings.time_offset_ms = None
            settings.time_sync_rtt_ms = None
            settings.time_sync_error = str(result.get("error") or "time sync failed")

    def _time_sync_note(self, settings: RushSettings) -> str:
        if not settings.time_sync_enabled:
            return "Time sync disabled."
        if settings.time_offset_ms is None:
            return f"Time sync failed; using local clock. {settings.time_sync_error}".strip()
        return (
            f"Time offset {settings.time_offset_ms:+.1f} ms "
            f"(RTT {settings.time_sync_rtt_ms or 0:.1f} ms)."
        )

    def _timing_note(self, settings: RushSettings) -> str:
        lead_seconds = settings.capture_settle_seconds
        parts = [self._time_sync_note(settings)]
        if settings.scheduled_start:
            parts.append(f"Launch lead includes capture settle {lead_seconds:.1f}s.")
        return " ".join(part for part in parts if part)

    def _delay_until(self, settings: RushSettings) -> float:
        scheduled_start = settings.scheduled_start
        if not scheduled_start:
            return 0.0
        try:
            parsed = datetime.fromisoformat(scheduled_start.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        now = datetime.now(parsed.tzinfo or timezone.utc)
        offset_seconds = (settings.time_offset_ms or 0.0) / 1000.0
        lead_seconds = settings.capture_settle_seconds
        return max(0.0, (parsed - now).total_seconds() - lead_seconds - offset_seconds)

    def _new_job_id(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"

    def _ps_quote(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"
