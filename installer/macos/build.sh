
#!/usr/bin/env bash
set -e

# Set variables
VERSION="1.0.0"
APP_NAME="NetSpeed"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/dist/v${VERSION}/macos"
PYTHON=python3

# Create build directory
mkdir -p "${BUILD_DIR}"

# Install requirements
cd "${PROJECT_ROOT}"
${PYTHON} -m pip install -r requirements.txt
${PYTHON} -m pip install pyinstaller

# Run PyInstaller for macOS Intel (x86_64)
# --target-architecture x86_64 ensures it's built for Intel
${PYTHON} -m PyInstaller \
    --noconfirm \
    --name "${APP_NAME}" \
    --windowed \
    --icon "${PROJECT_ROOT}/installer/macos/app.icns" \
    --target-architecture x86_64 \
    --add-data "${PROJECT_ROOT}/netspeed_tracker:netspeed_tracker" \
    --clean \
    --onefile \
    --distpath "${BUILD_DIR}" \
    --workpath "${PROJECT_ROOT}/build" \
    --specpath "${PROJECT_ROOT}/build" \
    "${PROJECT_ROOT}/run.pyw"

echo "Executable for macOS Intel created in ${BUILD_DIR}"
