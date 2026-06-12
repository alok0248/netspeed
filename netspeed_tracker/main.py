import sys, threading, time
from PyQt5 import QtWidgets, QtCore
from monitor import NetMonitor
from ui import SpeedOverlay
from tray import start_tray
import win32gui, win32api, win32con

def is_fullscreen():
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    fullscreen = False
    def enum_cb(hwnd, _):
        nonlocal fullscreen
        if win32gui.IsWindowVisible(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            w, h = rect[2] - rect[0], rect[3] - rect[1]
            if w == screen_w and h == screen_h:
                fullscreen = True
    win32gui.EnumWindows(enum_cb, None)
    return fullscreen

class Worker(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(float, float, float, bool)

    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.running = True

    def run(self):
        while self.running:
            dl, ul = self.monitor.sample()
            total = self.monitor.today_rx + self.monitor.today_tx
            is_full = is_fullscreen()
            self.update_signal.emit(dl, ul, total, is_full)
            time.sleep(1)

def run():
    try:
        print("Creating QApplication...")
        app = QtWidgets.QApplication(sys.argv)
        print("Creating overlay...")
        overlay = SpeedOverlay()
        print("Showing overlay...")
        overlay.show()
        print("Starting tray icon...")
        start_tray(app)
        print("Starting NetMonitor...")
        monitor = NetMonitor()
        
        worker = Worker(monitor)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        
        def update_ui(dl, ul, total, is_full):
            print(f"Update UI: dl={dl}, ul={ul}, total={total}, fullscreen={is_full}")
            overlay.update_text(dl, ul, total)
            # For testing, always keep it visible first!
            overlay.setVisible(True)
        
        worker.update_signal.connect(update_ui)
        thread.started.connect(worker.run)
        thread.start()
        
        print("Entering app exec loop...")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    run()
