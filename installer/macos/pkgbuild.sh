#!/usr/bin/env bash
set -e

VERSION="1.0.0"
APP_NAME="NetSpeed"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/dist/v${VERSION}/macos"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_BUNDLE="${SCRIPT_DIR}/${APP_NAME}.app"

# Clean up old bundle
rm -rf "${APP_BUNDLE}"

# Create .app bundle structure
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# Copy executable
if [ -f "${BUILD_DIR}/${APP_NAME}" ]; then
    cp "${BUILD_DIR}/${APP_NAME}" "${APP_BUNDLE}/Contents/MacOS/"
else
    echo "Error: Executable not found at ${BUILD_DIR}/${APP_NAME}. Did you run build.sh first?"
    exit 1
fi

# Copy icon if available
if [ -f "${SCRIPT_DIR}/app.icns" ]; then
    cp "${SCRIPT_DIR}/app.icns" "${APP_BUNDLE}/Contents/Resources/"
fi

# Minimal Info.plist
cat > "${APP_BUNDLE}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>NetSpeed</string>
    <key>CFBundleIdentifier</key><string>com.netspeed.app</string>
    <key>CFBundleName</key><string>NetSpeed</string>
    <key>CFBundleVersion</key><string>${VERSION}</string>
    <key>CFBundleShortVersionString</key><string>${VERSION}</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleSignature</key><string>????</string>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSUIElement</key><true/>
EOF

# Copy icon reference to Info.plist if available
if [ -f "${SCRIPT_DIR}/app.icns" ]; then
    /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string app" "${APP_BUNDLE}/Contents/Info.plist"
fi

# Create DMG
DMG_NAME="${APP_NAME}-${VERSION}-macos-intel.dmg"
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_BUNDLE}" -ov -format UDZO "${SCRIPT_DIR}/${DMG_NAME}"

# Move DMG to distribution folder
mv "${SCRIPT_DIR}/${DMG_NAME}" "${BUILD_DIR}/${DMG_NAME}"

# Clean up
rm -rf "${APP_BUNDLE}"

echo "DMG created at ${BUILD_DIR}/${DMG_NAME}"