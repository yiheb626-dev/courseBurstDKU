from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import unquote, urlparse

from ..core.models import (
    MAX_SAFE_REQUESTS_PER_SECOND,
    MAX_VERIFIED_REQUESTS_PER_SECOND,
    is_rate_limit_override_valid,
)
from ..services.browser_launcher import BrowserLauncher
from ..services.cart_reader import CartReader
from ..services.profile_cleaner import ProfileCleaner
from ..services.task_manager import TaskManager
from ..services.time_sync import DEFAULT_TIME_SERVER, TimeSyncClient


PROJECT_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[3]
WEB_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = WEB_ROOT / "static"
TEMPLATE_ROOT = WEB_ROOT / "templates"
TASK_MANAGER = TaskManager(PROJECT_ROOT)
BROWSER_LAUNCHER = BrowserLauncher(PROJECT_ROOT)
CART_READER = CartReader()
PROFILE_CLEANER = ProfileCleaner(PROJECT_ROOT)
TIME_SYNC_CLIENT = TimeSyncClient()


class CourseRushHandler(BaseHTTPRequestHandler):
    server_version = "CourseRushWeb/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self._send_file(TEMPLATE_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            relative = unquote(path[len("/static/") :])
            self._send_static(relative)
            return
        if path == "/api/defaults":
            self._send_json(
                {
                    "settings": self._default_settings(),
                    "browser": BROWSER_LAUNCHER.defaults(),
                }
            )
            return
        if path == "/api/browser/defaults":
            self._send_json({"browser": BROWSER_LAUNCHER.defaults()})
            return
        if path == "/api/jobs":
            self._send_json(TASK_MANAGER.list_jobs())
            return
        if path.startswith("/api/jobs/"):
            job_id = path.split("/", 3)[3]
            payload = TASK_MANAGER.get_job(job_id)
            if payload.get("error") == "not_found":
                self._send_json(payload, HTTPStatus.NOT_FOUND)
            else:
                self._send_json(payload)
            return
        self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/jobs":
            payload = self._read_json()
            result = TASK_MANAGER.create_job(payload.get("settings", payload))
            status = HTTPStatus.BAD_REQUEST if result.get("error") else HTTPStatus.CREATED
            self._send_json(result, status)
            return
        if path == "/api/browser/launch":
            payload = self._read_json()
            result = BROWSER_LAUNCHER.launch(payload.get("browser", payload))
            status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
            self._send_json(result, status)
            return
        if path == "/api/cart/read":
            payload = self._read_json()
            result = CART_READER.read(payload.get("settings", payload))
            status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
            self._send_json(result, status)
            return
        if path == "/api/time/sync":
            payload = self._read_json()
            result = TIME_SYNC_CLIENT.measure(str(payload.get("server") or ""))
            status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
            self._send_json(result, status)
            return
        if path == "/api/rate-limit/verify":
            payload = self._read_json()
            ok = is_rate_limit_override_valid(str(payload.get("code") or ""))
            result = {
                "ok": ok,
                "max_requests_per_second": MAX_VERIFIED_REQUESTS_PER_SECOND
                if ok
                else MAX_SAFE_REQUESTS_PER_SECOND,
                "message": "Override code verified." if ok else "Invalid override code.",
            }
            status = HTTPStatus.OK if ok else HTTPStatus.UNAUTHORIZED
            self._send_json(result, status)
            return
        if path == "/api/browser/clean-cache":
            result = PROFILE_CLEANER.clean_cache()
            status = HTTPStatus.OK if result.get("ok") else HTTPStatus.CONFLICT
            self._send_json(result, status)
            return
        if path == "/api/history/clear":
            browser_result = PROFILE_CLEANER.clear_browser_history()
            task_result = TASK_MANAGER.clear_history()
            result = {
                "ok": bool(browser_result.get("ok")) and bool(task_result.get("ok")),
                "message": "History cleared.",
                "removed_bytes": int(browser_result.get("removed_bytes", 0))
                + int(task_result.get("removed_bytes", 0)),
                "browser": browser_result,
                "tasks": task_result,
            }
            status = HTTPStatus.OK if result["ok"] else HTTPStatus.CONFLICT
            self._send_json(result, status)
            return
        if path.startswith("/api/jobs/") and path.endswith("/stop"):
            parts = path.split("/")
            if len(parts) >= 4:
                result = TASK_MANAGER.stop_job(parts[3])
                status = HTTPStatus.NOT_FOUND if result.get("error") == "not_found" else HTTPStatus.OK
                self._send_json(result, status)
                return
        self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {format % args}")

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, relative: str) -> None:
        target = (STATIC_ROOT / relative).resolve()
        try:
            target.relative_to(STATIC_ROOT.resolve())
        except ValueError:
            self._send_json({"error": "invalid_static_path"}, HTTPStatus.BAD_REQUEST)
            return
        self._send_file(target)

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        guessed_type = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", guessed_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _default_settings(self) -> Dict[str, Any]:
        return {
            "cdp_url": "http://127.0.0.1:9222",
            "page_url_keyword": "dkuhub.dku.edu.cn",
            "capture_keywords": "IScript_Enroll",
            "capture_timeout": 120,
            "capture_settle_seconds": 1.5,
            "auto_click_enroll": True,
            "strategy_mode": "smooth",
            "smooth_requests_per_second": 2.5,
            "smooth_total_requests": 50,
            "burst_count": 5,
            "burst_rounds_per_second": 0.9,
            "burst_rounds": 10,
            "hybrid_burst_count": 5,
            "hybrid_burst_rounds": 2,
            "hybrid_burst_rounds_per_second": 0.9,
            "hybrid_smooth_requests_per_second": 2.5,
            "hybrid_total_requests": 50,
            "rate_limit_override_code": "",
            "keep_session_alive": True,
            "time_sync_enabled": True,
            "time_sync_server": DEFAULT_TIME_SERVER,
            "time_offset_ms": "",
            "time_sync_rtt_ms": "",
            "time_sync_checked_at": "",
            "time_sync_error": "",
            "scheduled_start": "",
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the course rush web dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("COURSE_RUSH_WEB_PORT", "8765")))
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Start the web server without opening the dashboard in a browser.",
    )
    return parser.parse_args()


def _dashboard_url(host: str, port: int) -> str:
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{browser_host}:{port}/"


def _open_dashboard(url: str) -> None:
    try:
        if os.name == "nt":
            edge_executable = str(BROWSER_LAUNCHER.defaults().get("edge_executable") or "")
            if edge_executable and Path(edge_executable).exists():
                subprocess.Popen(
                    [edge_executable, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            os.startfile(url)  # type: ignore[attr-defined]
            return
        webbrowser.open(url, new=0)
    except Exception as exc:
        print(f"Could not open browser automatically: {exc}")


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CourseRushHandler)
    url = _dashboard_url(args.host, args.port)
    print(f"Course Rush Web is running: {url}")
    if not args.no_open:
        threading.Timer(0.5, _open_dashboard, args=(url,)).start()
        print("Opening dashboard in your default browser...")
    else:
        print("Auto-open disabled. Open the dashboard URL manually.")
    print("Press Ctrl+C to stop the web server. Running CLI job windows are independent.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
