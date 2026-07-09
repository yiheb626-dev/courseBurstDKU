# Course Rush Web

Course Rush Web is a local web dashboard for running a dedicated course-enrollment automation workflow. It starts a separate Microsoft Edge profile, connects to the enrollment page through Chrome DevTools Protocol (CDP), captures a real enroll request, and replays it according to user-configured safety limits and strategies.

This project is only for sharing purposes. The author is not responsible for ANY consequences caused by the users of this web app. They should be fully aware of the capabilities as well as its limitations of this project. Any attempt of violating the school regulations using this app is strongly discouraged.

## Features

- Starts a dedicated Microsoft Edge window with `--remote-debugging-port` and an isolated `--user-data-dir`.
- Connects to the enrollment system page through Edge CDP after the user signs in.
- Reads course rows from the Shopping Cart page when possible.
- Allows manual course entry when automatic cart reading is incomplete.
- Captures the real enroll request by clicking `Enroll In Selected Classes` once automatically when possible.
- Falls back to manual click capture if the enroll button cannot be detected.
- Provides configurable capture keywords, capture timeout, capture settle time, auto-start time, and keep-alive behavior.
- Supports Smooth, Burst, and Hybrid course-rush strategies.
- Uses conservative defaults: Smooth mode at 2.5 requests per second and 50 total requests.
- Enforces a default safety limit of 5 requests per second.
- Allows higher limits only after local Override Code verification, up to 50 requests per second.
- Keeps Hybrid locked until Override Code verification succeeds.
- Lets Burst use default parameters without verification, while editing Burst parameters requires verification.
- Supports Tencent NTP time calibration for scheduled starts.
- Uses the formula: `CLI start time = auto start time - capture settle seconds - NTP offset`.
- Launches a separate PowerShell CLI window for the actual task.
- Synchronizes job status, round count, success status, and CLI log tail back to the web dashboard.
- Includes a Chinese/English language selector with `localStorage` persistence.

## What This Project Does Not Store

This repository should not contain credentials, cookies, session data, private keys, encryption secrets, or Override Code values.

Runtime browser state and job logs are generated locally and are ignored by Git:

```text
data/
browser_profile/
__pycache__/
```

Before publishing to GitHub, review staged files and make sure no private runtime files are included.

## Project Structure

```text
courseBurstDKU/
  legacy/                         # Legacy script copies and notes
  run_web.py                      # Web dashboard entry point
  requirements.txt                # Python dependencies
  src/course_rush_web/
    cli.py                        # Standalone CLI task entry point
    core/
      burst_engine.py             # Request capture and replay logic
      models.py                   # Settings and status models
    services/
      browser_launcher.py         # Dedicated Edge/CDP launcher
      cart_reader.py              # Shopping Cart course reader
      job_store.py                # Job config, status, and log storage
      task_manager.py             # Job creation, scheduling, CLI launch, stop
      time_sync.py                # NTP time offset measurement
    web/
      server.py                   # Standard-library HTTP JSON server
      templates/index.html        # Web UI
      static/app.js               # Frontend logic and i18n
      static/styles.css           # Styles
```

## Requirements

- Windows
- Python 3.10 or newer
- Microsoft Edge
- Playwright Chromium runtime

Install dependencies:

```powershell
cd "D:\PycharmProjects\problemSolving\courseBurstDKU"
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Start the Web Dashboard

```powershell
cd "D:\PycharmProjects\problemSolving\courseBurstDKU"
python .\run_web.py
```

The dashboard opens automatically in your default browser.

Default URL:

```text
http://127.0.0.1:8765/
```

Use another port if needed:

```powershell
python .\run_web.py --port 8777
```

Start the server without opening a browser:

```powershell
python .\run_web.py --no-open
```

## Usage Flow

1. Open the web dashboard.
2. Go to `Dedicated Browser`.
3. Confirm the Edge executable path, CDP port, start URL, and user data directory.
4. Click `Start Dedicated Browser`.
5. In the dedicated Edge window, sign in to the enrollment system.
6. Stay on the Shopping Cart or enroll page.
7. Click `Read Shopping Cart Courses` and confirm the course table.
8. Add courses manually if automatic reading misses anything.
9. Configure strategy and schedule settings.
10. Click `Create and Run Job`.
11. Watch the PowerShell CLI window and the dashboard status panel.

The course table is only for user confirmation. The actual replay target is still based on the captured enroll request URL, headers, and body from Edge.

## Strategy Notes

### Smooth

Smooth mode sends one request at a fixed interval. It is the default mode and uses conservative parameters.

### Burst

Burst mode sends multiple concurrent requests per round. Without Override Code verification, Burst can only use default parameters.

### Hybrid

Hybrid mode starts with a short Burst phase, then switches to Smooth mode. It stays locked until Override Code verification succeeds.

## Time Calibration

When NTP time sync is enabled, the app measures the official time offset before creating a scheduled job.

The launch formula is:

```text
CLI start time = auto start time - capture settle seconds - NTP offset
```

Scheduling within 10 minutes is recommended. Longer waits may cause the login session to expire. When keep-alive is enabled, the app refreshes the browser page every 10 minutes while waiting.

## Runtime Data

Job data is written to:

```text
courseBurstDKU/data/jobs/*.config.json
courseBurstDKU/data/jobs/*.status.json
courseBurstDKU/data/logs/*.log
```

Dedicated browser data is written to:

```text
courseBurstDKU/browser_profile/
```

These directories are runtime-only and should not be committed.

## GitHub Publishing Checklist

Before uploading:

- Confirm `.gitignore` excludes runtime and local-only files.
- Do not commit `data/`.
- Do not commit `browser_profile/`.
- Do not commit cookies, sessions, logs, screenshots, local credentials, or environment files.
- Do not publish any Override Code value or verification secret.
- Review `git status` before every commit.

Suggested `.gitignore` entries:

```gitignore
__pycache__/
*.py[cod]
data/
browser_profile/
.venv/
.env
.idea/
```

If you want to publish only the web project and not the legacy copy, also ignore:

```gitignore
legacy/
```

## Development Checks

Check frontend syntax:

```powershell
node --check src\course_rush_web\web\static\app.js
```

Run the dashboard locally after frontend changes:

```powershell
python .\run_web.py --no-open
```

Then open:

```text
http://127.0.0.1:8765/
```

## Packaging for Windows

This project is prepared for PyInstaller `onedir` packaging. The packaged executable reuses the same binary for both the web dashboard and CLI worker mode.

Install PyInstaller:

```powershell
python -m pip install pyinstaller
```

Build a console version first:

```powershell
.\build_exe.ps1
```

The output is:

```text
dist\CourseRushWeb\CourseRushWeb.exe
```

Distribute the entire folder:

```text
dist\CourseRushWeb\
```

Do not distribute only `CourseRushWeb.exe`, because the `onedir` build needs the bundled support files beside it.

After the console version is tested, you can build a no-console version:

```powershell
.\build_exe.ps1 -NoConsole
```

Packaging notes:

- The build does not include `data/`, `browser_profile/`, logs, cookies, or session files.
- The build does not include a bundled Chromium browser.
- Microsoft Edge must be installed on the target Windows machine.
- Playwright is bundled for CDP control, but it connects to the user's local Edge instance.
- Runtime data is created next to the packaged executable folder at first run.
- `onedir` is recommended over `onefile` for faster startup, easier debugging, and fewer antivirus false positives.

## Security Notes

This tool is intended to run locally. Keep the dashboard bound to `127.0.0.1` unless you fully understand the security implications of exposing it to a network.

Do not share browser profiles, session files, cookies, logs, or any local verification secrets. The repository should contain source code and documentation only.
