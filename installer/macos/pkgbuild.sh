#!/usr/bin/env bash
set -e
VERSION=1.0.0
APP_NAME="NetSpeed"
# Paths
BUILD_DIR="$(pwd)/../../dist/v${VERSION}/macos"
APP_BUNDLE="${APP_NAME}.app"

# Create .app bundle structure
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
cp "${BUILD_DIR}/NetSpeed" "${APP_BUNDLE}/Contents/MacOS/"

# Minimal Info.plist
cat > "${APP_BUNDLE}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>NetSpeed</string>
    <key>CFBundleIdentifier</key><string>com.example.netspeed</string>
    <key>CFBundleName</key><string>NetSpeed</string>
    <key>CFBundleVersion</key><string>${VERSION}</string>
</dict>
</plist>
EOF

# Create DMG
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_BUNDLE}" -ov -format UDZO "${DMG_NAME}"

# Move DMG to distribution folder
mv "${DMG_NAME}" "${BUILD_DIR}/${DMG_NAME}"

echo "DMG created at ${BUILD_DIR}/${DMG_NAME}"