# getcourses_browser_auth

This version works with your own already-open Microsoft Edge window.
It does not open a new browser.

## What it does

1. Connects to your running Edge session via CDP.
2. Waits for your manual enroll click request (for example `IScript_Enroll`).
3. Captures URL/method/headers/body from that real request.
4. Replays the captured request in burst mode from the same logged-in tab context.

## Install

```powershell
cd "D:\PycharmProjects\problemSolving"
.\.venv\Scripts\activate
python -m pip install -r ".\getcourses_browser_auth\requirements.txt"
python -m playwright install chromium
```

## Start Edge in CDP mode (required)

Close all Edge windows first, then run:

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="D:\edge-cdp-profile"
```

Then open the course page in that Edge window and log in.

## Run capture + replay

```powershell
cd "D:\PycharmProjects\problemSolving"
.\.venv\Scripts\activate
python ".\getcourses_browser_auth\browser_context_burst.py" `
  --cdp-url "http://127.0.0.1:9222" `
  --page-url-keyword "dkuhub.dku.edu.cn" `
  --capture-keywords "IScript_" `
  --capture-settle-seconds 1.5 `
  --capture-timeout 120 `
  --burst-count 20 `
  --bursts-per-second 1 `
  --rounds 100
```

After the script prints `Now click the enroll button...`, click enroll in Edge.
Once request is captured, replay starts automatically.
Replay output is simplified to:
- `enrolled=YES/NO`
- `text: ...` (server message text)
If multiple classes are included in one enroll request, script stops only when all target classes are enrolled.

Rate control:
- `--bursts-per-second`: target burst rounds per second
- `--rounds`: total rounds (`0` means infinite)
- `--round-interval`: fallback delay used only when `--bursts-per-second` is `0`

## Important notes

- You must click enroll after the script starts waiting.
- If your click triggers multiple APIs, script will prioritize `IScript_Enroll` automatically.
- If no request is captured, widen `--capture-keywords` (for example `IScript_`).
- Keep actions compliant with your school's system policy.
