# Round Control Guide

This guide explains how to control replay rate and loop count in:

- `D:\PycharmProjects\problemSolving\getcourses_browser_auth\browser_context_burst.py`

## Control arguments

- `--bursts-per-second`  
  Target burst rounds per second.  
  Example: `--bursts-per-second 2` means ~2 rounds every second.

- `--rounds`  
  Total rounds to run.  
  `0` means infinite loop (until manual stop or enrollment success condition).

- `--round-interval`  
  Delay between rounds in seconds.  
  Used only when `--bursts-per-second` is `0`.

## Current code locations

- `browser_context_burst.py:274` -> `--rounds`
- `browser_context_burst.py:280` -> `--round-interval`
- `browser_context_burst.py:286` -> `--bursts-per-second`
- `browser_context_burst.py:405` -> convert bursts/s to interval (`1.0 / bursts_per_second`)
- `browser_context_burst.py:468` -> actual pacing sleep logic

## Recommended usage

- 2 bursts per second, run 100 rounds:

```powershell
python ".\getcourses_browser_auth\browser_context_burst.py" --bursts-per-second 2 --rounds 100
```

- Continuous run, no delay (max speed):

```powershell
python ".\getcourses_browser_auth\browser_context_burst.py" --bursts-per-second 0 --rounds 0
```

- Continuous run, one burst per second:

```powershell
python ".\getcourses_browser_auth\browser_context_burst.py" --bursts-per-second 1 --rounds 0
```

## Manual stop

Press `Ctrl + C` in terminal/console to stop immediately.
