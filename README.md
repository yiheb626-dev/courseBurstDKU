# Course Burst DKU

Course Burst DKU is a local web dashboard for running a dedicated course-enrollment automation workflow. It starts a separate Microsoft Edge profile, connects to the enrollment page through Chrome DevTools Protocol (CDP), captures a real DKU Hub enroll request, and replays it according to user-configured safety limits and strategies.

Current version: [yiheb626-dev/courseBurstDKU](https://github.com/yiheb626-dev/courseBurstDKU).

**Disclaimer: This project is provided for local educational and personal workflow automation purposes only. It is strongly recommended by the author to follow the school regulations and do not use it to overload, disrupt, or attack any service. The author does not provide any guarantee of enrollment success or assume responsibility for misuse.**

## How to Run

### Recommended: Download the EXE Package

The recommended way to run this project is to download the packaged Windows build from the GitHub Releases page:

[Download from Releases](https://github.com/yiheb626-dev/courseBurstDKU/releases)

After downloading:

1. Extract the package.
2. Run `CourseRushWeb.exe`.
3. Open the local dashboard if it does not open automatically.

The packaged version is designed to use the Microsoft Edge installation on your Windows machine. Do not move only the `.exe` file out of the extracted folder; keep the package folder intact.

### Alternative: Run from Command Line

Requirements:

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

Start the web dashboard:

```powershell
python .\run_web.py
```

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

## Strategy Notes

### Smooth

Smooth mode sends one request at a fixed interval. It is the default mode and uses conservative parameters as default.

### Burst

Burst mode sends multiple concurrent requests per round near instantly. Without Override Code verification, Burst can only use default parameters.

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

These directories are runtime-only and should not be committed or shared.

## Security Notes

This tool is intended to run locally. Keep the dashboard bound to `127.0.0.1` unless you fully understand the security implications of exposing it to a network.

Do not share browser profiles, session files, cookies, logs, screenshots, local credentials, environment files, or any local verification secrets. The repository should contain source code and documentation only.

## What This Project Does Not Share

This project does not share or upload credentials, cookies, session data, private keys, encryption secrets, Override Code values, browser profiles, or job logs.

Runtime browser state and job logs are generated locally:

```text
data/
browser_profile/
```

Review files before publishing, packaging, or sending this project to anyone else.
