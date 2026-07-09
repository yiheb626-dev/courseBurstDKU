from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.models import JobConfig, JobStatus


class JobStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.jobs_dir = self.data_dir / "jobs"
        self.logs_dir = self.data_dir / "logs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def config_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.config.json"

    def status_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.status.json"

    def log_path(self, job_id: str) -> Path:
        return self.logs_dir / f"{job_id}.log"

    def save_config(self, config: JobConfig) -> None:
        self._write_json(self.config_path(config.job_id), config.to_dict())

    def load_config(self, job_id: str) -> Optional[JobConfig]:
        path = self.config_path(job_id)
        if not path.exists():
            return None
        return JobConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save_status(self, status: JobStatus) -> None:
        self._write_json(self.status_path(status.job_id), status.to_dict())

    def load_status(self, job_id: str) -> Optional[JobStatus]:
        path = self.status_path(job_id)
        if not path.exists():
            return None
        return JobStatus.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_statuses(self) -> List[Dict[str, Any]]:
        statuses: List[Dict[str, Any]] = []
        for path in sorted(self.jobs_dir.glob("*.status.json"), reverse=True):
            try:
                statuses.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return statuses

    def read_log_tail(self, job_id: str, max_lines: int = 250) -> str:
        path = self.log_path(job_id)
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-max_lines:])

    def clear_history(self) -> Dict[str, Any]:
        removed_items: List[str] = []
        errors: List[str] = []
        removed_bytes = 0

        for root in (self.jobs_dir, self.logs_dir):
            for path in root.glob("*"):
                if not path.is_file():
                    continue
                try:
                    size = path.stat().st_size
                    path.unlink()
                    removed_bytes += size
                    removed_items.append(str(path.relative_to(self.data_dir)))
                except Exception as exc:
                    errors.append(f"{path.relative_to(self.data_dir)}: {exc}")

        return {
            "ok": not errors,
            "message": "Task history cleared." if not errors else "Task history cleared with some locked files.",
            "removed_bytes": removed_bytes,
            "removed_items": removed_items,
            "errors": errors,
        }

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(path)
