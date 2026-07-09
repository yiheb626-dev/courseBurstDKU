from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from course_rush_web.web.server import main


def dispatch() -> int:
    if "--run-cli" in sys.argv:
        sys.argv.remove("--run-cli")
        from course_rush_web.cli import main as cli_main

        return cli_main()
    return main()


if __name__ == "__main__":
    raise SystemExit(dispatch())
