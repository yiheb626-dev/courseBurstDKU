param(
    [switch]$NoConsole
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$pyInstallerArgs = @(
    "--clean",
    "--noconfirm",
    "--onedir",
    "--name", "CourseRushWeb",
    "--paths", "src",
    "--collect-all", "playwright",
    "--add-data", "src\course_rush_web\web\templates;course_rush_web\web\templates",
    "--add-data", "src\course_rush_web\web\static;course_rush_web\web\static",
    "run_web.py"
)

if ($NoConsole) {
    $pyInstallerArgs = @("--noconsole") + $pyInstallerArgs
}

python -m PyInstaller @pyInstallerArgs

Write-Host ""
Write-Host "Build complete: dist\CourseRushWeb\CourseRushWeb.exe"
Write-Host "Distribute the whole dist\CourseRushWeb folder, not only the exe."
