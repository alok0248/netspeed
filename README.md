# NetSpeed Tracker

A small Windows utility that displays real‑time download/upload speed and today's total data usage in a always‑on‑top overlay.

## Features
- Live download/upload speeds (Mbps) with arrow symbols
- Daily total data usage
- Draggable and resizable overlay that remembers its position
- Always‑on‑top, semi‑transparent background
- System‑tray icon with Quit option
- Simple double‑click launcher (`run.bat`)

## Requirements
- Windows 10/11
- Python 3.9+ with the packages listed in `requirements.txt`

## Installation
```batch
# Clone the repo
git clone <repo-url>
cd netspeed

# Create virtual environment
python -m venv venv
.env\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run the app
run.bat
```

## Usage
- Drag the overlay to reposition it; the position is saved automatically.
- Double‑click the tray icon to quit.
- The overlay stays visible at all times (fullscreen‑hiding logic disabled).

## License
MIT License
