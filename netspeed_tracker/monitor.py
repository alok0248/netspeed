import psutil, time, datetime
import ctypes
import win32gui
import win32con
from PyQt5 import QtCore


def format_data_size(bytes_total):
    """Format bytes into human-readable units (MB, GB, etc.)."""
    if bytes_total < 1024:
        return f"{bytes_total} B"
    elif bytes_total < 1024 * 1024:
        kb = bytes_total / 1024
        return f"{kb:.2f} KB"
    elif bytes_total < 1024 * 1024 * 1024:
        mb = bytes_total / (1024 * 1024)
        return f"{mb:.2f} MB"
    else:
        gb = bytes_total / (1024 * 1024 * 1024)
        return f"{gb:.2f} GB"


def format_speed(bytes_per_second, unit='Mbps'):
    """Format speed (bytes per second) into specified unit (B/s, Kbps, Mbps, Gbps)."""
    # Convert bits per second (since network speeds are usually in bits)
    bits_per_second = bytes_per_second * 8
    
    if unit == 'B/s':
        return f"{bytes_per_second:.2f} B/s"
    elif unit == 'Kbps':
        kbps = bits_per_second / 1000
        return f"{kbps:.2f} Kbps"
    elif unit == 'Mbps':
        mbps = bits_per_second / (1000 * 1000)
        return f"{mbps:.2f} Mbps"
    elif unit == 'Gbps':
        gbps = bits_per_second / (1000 * 1000 * 1000)
        return f"{gbps:.2f} Gbps"
    else:
        # Default to Mbps
        mbps = bits_per_second / (1000 * 1000)
        return f"{mbps:.2f} Mbps"


class NetMonitor:
    def __init__(self):
        self.settings = QtCore.QSettings('NetSpeed', 'Overlay')
        self.last = psutil.net_io_counters()
        
        # Load today's data from settings (persistent)
        self._load_today_data()
        
        self.user32 = ctypes.windll.user32
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        
        # Start midnight reset thread
        import threading
        threading.Thread(target=self._reset_at_midnight, daemon=True).start()

    def _load_today_data(self):
        """Load today's data from persistent storage, reset if date changed."""
        saved_date = self.settings.value('data_date', None)
        today_date_str = datetime.date.today().isoformat()
        
        if saved_date == today_date_str:
            self.today_rx = self.settings.value('today_rx', 0, type=int)
            self.today_tx = self.settings.value('today_tx', 0, type=int)
        else:
            self.today_rx = 0
            self.today_tx = 0
            self.settings.setValue('data_date', today_date_str)
            self.settings.setValue('today_rx', 0)
            self.settings.setValue('today_tx', 0)

    def _save_today_data(self):
        """Save today's data to persistent storage."""
        self.settings.setValue('today_rx', self.today_rx)
        self.settings.setValue('today_tx', self.today_tx)

    def _reset_at_midnight(self):
        while True:
            now = datetime.datetime.now()
            next_mid = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            time.sleep((next_mid - now).total_seconds())
            
            # Reset for new day
            self.today_rx = 0
            self.today_tx = 0
            today_date_str = datetime.date.today().isoformat()
            self.settings.setValue('data_date', today_date_str)
            self._save_today_data()

    def _is_fullscreen(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # Check if window covers entire screen
            covers_full_screen = (left <= 0 and 
                                  top <= 0 and 
                                  right >= self.screen_width and 
                                  bottom >= self.screen_height)
            
            if covers_full_screen:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_VISIBLE:
                    classname = win32gui.GetClassName(hwnd)
                    # Skip desktop and taskbar windows
                    if classname not in ["Shell_TrayWnd", "Progman", "WorkerW", "Shell_SecondaryTrayWnd"]:
                        return True
            return False
        except Exception as e:
            print(f"Error in full screen detection: {e}")
            return False

    def sample(self):
        try:
            cur = psutil.net_io_counters()
            dl = cur.bytes_recv - self.last.bytes_recv
            ul = cur.bytes_sent - self.last.bytes_sent
            
            # Ensure no negative values (can happen with interface resets)
            if dl < 0:
                dl = 0
            if ul < 0:
                ul = 0
                
            self.last = cur
            self.today_rx += dl
            self.today_tx += ul
            
            total = self.today_rx + self.today_tx
            self._save_today_data()
            fullscreen = self._is_fullscreen()
            return dl, ul, total, fullscreen
        except Exception as e:
            print(f"Error retrieving network data: {e}")
            return 0, 0, self.today_rx + self.today_tx, False
