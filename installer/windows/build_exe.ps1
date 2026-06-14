# Build a single‑file Windows executable for NetSpeed
# ---------------------------------------------------
# Prerequisite: PyInstaller must be installed in the current Python environment.
# This script creates a self‑contained .exe with all required dependencies
# and places it in the installer\windows directory.

$projectRoot = Resolve-Path "$PSScriptRoot\..\.."
$srcPath = Join-Path $projectRoot "run.py"
$distDir = Join-Path $projectRoot "installer\windows"

# Ensure the output directory exists
if (-Not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

# Run PyInstaller to build a one-file executable
# --onefile creates a single exe, --noconsole hides the console window.
# Adjust additional options as needed (e.g., icon, hidden imports).
python -m PyInstaller `
    --onefile `
    --noconsole `
    --name NetSpeed `
    --distpath $distDir `
    --collect-submodules netspeed_tracker `
    --hidden-import netspeed_tracker.monitor `
    --hidden-import netspeed_tracker.ui `
    --hidden-import netspeed_tracker.tray `
    $srcPath

Write-Host "Executable built and placed at: $distDir\NetSpeed.exe"
