# NetSpeed Tracker
A small Windows utility that displays real‑time download/upload speed and today's total data usage in an always‑on‑top overlay.

## Features
- Live download/upload speeds with arrow symbols (supports B/s, Kbps, Mbps, Gbps)
- Daily total data usage (auto-resets at midnight)
- Draggable overlay that remembers its position
- Always-on-top display
- Three themes:
  - **Solid Theme**: Custom background color with adjustable transparency
  - **Glass Theme**: Semi-transparent black with subtle border
  - **Transparent Theme**: Fully transparent background
- Right-click menu with text size, speed unit, theme, and position options
- System tray icon
- Auto-hides when a full-screen app is active
- Persistent settings saved between sessions

## Requirements
- Windows 10/11
- Python 3.9 or newer

## Quick Start (for First Time Users)
Just run the `firsttime.bat` file and it will automatically set up everything for you!

## Manual Installation
1. Clone or download the repo
2. Create and activate a virtual environment
3. Install dependencies
4. Run the app!

```batch
# Clone the repo
git clone https://github.com/alok0248/netspeed.git
cd netspeed

# Run firsttime.bat for easy setup
firsttime.bat

# Or do it manually
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
run.bat
```

## Usage
- Drag the overlay to reposition it; the position is saved automatically
- Right-click the overlay to open the menu with all options
- Click "Fix Position" in the menu to lock/unlock dragging
- Use the theme menu to switch themes and customize colors/opacity
- The overlay will hide when a full-screen app is active and show again when it exits
- Click "Exit" in the menu to quit the app

## License
MIT License
