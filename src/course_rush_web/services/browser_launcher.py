from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import parse, request


DEFAULT_EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


class BrowserLauncher:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.default_profile_dir = project_root / "browser_profile"
        self._process: Optional[subprocess.Popen[Any]] = None

    def defaults(self) -> Dict[str, Any]:
        return {
            "edge_executable": self._find_edge_executable(),
            "remote_debugging_port": 9222,
            "user_data_dir": str(self.default_profile_dir),
            "start_url": "https://dkuhub.dku.edu.cn",
        }

    def launch(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        if os.name != "nt":
            return {
                "ok": False,
                "message": "Automatic Edge launch is currently implemented for Windows only.",
            }

        edge_executable = str(raw.get("edge_executable") or "").strip() or self._find_edge_executable()
        if not edge_executable:
            return {
                "ok": False,
                "message": "Microsoft Edge executable was not found. Fill the Edge path manually.",
            }

        edge_path = Path(edge_executable)
        if not edge_path.exists():
            return {"ok": False, "message": f"Edge executable does not exist: {edge_executable}"}

        try:
            port = int(float(raw.get("remote_debugging_port") or 9222))
        except (TypeError, ValueError):
            port = 9222
        port = max(1, min(65535, port))

        user_data_dir = str(raw.get("user_data_dir") or self.default_profile_dir).strip()
        profile_path = Path(user_data_dir)
        profile_path.mkdir(parents=True, exist_ok=True)

        start_url = str(raw.get("start_url") or "https://dkuhub.dku.edu.cn").strip()
        if start_url and "://" not in start_url:
            start_url = "https://" + start_url

        command: List[str] = [
            str(edge_path),
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_path}",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-extensions",
            "--disable-sync",
            "--disable-session-crashed-bubble",
            "--hide-crash-restore-bubble",
            "--no-default-browser-check",
            "--no-first-run",
        ]
        if start_url:
            command.append(start_url)

        try:
            self._process = subprocess.Popen(command)
            closed_blank_tabs = self._close_extra_blank_tabs(port)
        except Exception as exc:
            return {"ok": False, "message": f"Failed to launch Edge: {exc}"}

        return {
            "ok": True,
            "message": "Dedicated Edge window launched.",
            "pid": self._process.pid,
            "closed_blank_tabs": closed_blank_tabs,
            "cdp_url": f"http://127.0.0.1:{port}",
            "start_url": start_url,
            "user_data_dir": str(profile_path),
            "edge_executable": str(edge_path),
        }

    def _find_edge_executable(self) -> str:
        for candidate in DEFAULT_EDGE_PATHS:
            if Path(candidate).exists():
                return candidate
        return ""

    def _close_extra_blank_tabs(self, port: int) -> int:
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            pages = self._list_cdp_pages(port)
            if not pages:
                time.sleep(0.2)
                continue

            has_real_page = any(
                page.get("type") == "page" and not self._is_blank_page_url(str(page.get("url") or ""))
                for page in pages
            )
            if not has_real_page:
                time.sleep(0.2)
                continue

            closed = 0
            for page in pages:
                target_id = str(page.get("id") or "")
                page_url = str(page.get("url") or "")
                if page.get("type") == "page" and target_id and self._is_blank_page_url(page_url):
                    closed += self._close_cdp_page(port, target_id)
            return closed
        return 0

    def _list_cdp_pages(self, port: int) -> List[Dict[str, Any]]:
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=0.4) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _close_cdp_page(self, port: int, target_id: str) -> int:
        quoted_target_id = parse.quote(target_id, safe="")
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/json/close/{quoted_target_id}", timeout=0.4):
                return 1
        except Exception:
            return 0

    def _is_blank_page_url(self, page_url: str) -> bool:
        normalized = page_url.strip().lower().rstrip("/")
        return normalized in {"", "about:blank", "edge://newtab", "chrome://newtab"}
