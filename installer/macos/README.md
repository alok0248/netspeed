
# NetSpeed macOS Build Instructions

## Prerequisites
- macOS (Intel or Apple Silicon with Rosetta)
- Python 3.8 or higher
- Xcode command-line tools (for hdiutil, etc.)

## Building
1. (Optional) Add an icon: Save your app icon as `app.icns` in this directory.
2. Make the scripts executable:
   ```bash
   chmod +x build.sh
   chmod +x pkgbuild.sh
   ```
3. Run the build script:
   ```bash
   ./build.sh
   ```
4. (Optional) Create a DMG installer:
   ```bash
   ./pkgbuild.sh
   ```

## Output
- The executable will be in `../../dist/v1.0.0/macos/`
- The DMG installer (if created) will be in the same directory
