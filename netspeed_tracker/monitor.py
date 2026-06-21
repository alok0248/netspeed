
import sys
import sqlite3
import os
import psutil
import time
import datetime
import threading
import ctypes
from collections import defaultdict
from pathlib import Path
from PyQt5 import QtCore

# Import Windows-specific modules only on Windows
if sys.platform == "win32":
    import win32gui
    import win32con
from netspeed_tracker.process_monitor import ProcessMonitor


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
        self.usage_lock = threading.Lock()
        self.db_path = self._get_db_path()
        self._init_db()
        
        # Initialize process monitor
        self.process_monitor = ProcessMonitor()
        
        # Load today's data from persistent storage (settings and DB)
        self._load_today_data()
        
        # Load bandwidth limit (in bytes, default 100 GB)
        saved_limit = self.settings.value('bandwidth_limit')
        if saved_limit is None:
            self.bandwidth_limit = 100 * 1024 * 1024 * 1024  # 100 GB default
        else:
            try:
                self.bandwidth_limit = int(saved_limit)
            except (ValueError, TypeError):
                self.bandwidth_limit = 100 * 1024 * 1024 * 1024
        self.settings.setValue('bandwidth_limit', self.bandwidth_limit)
        
        self.user32 = ctypes.windll.user32
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        
        # Start midnight reset thread
        threading.Thread(target=self._reset_at_midnight, daemon=True).start()

    def _get_db_path(self):
        """Return the persistent SQLite path used by the browser dashboard."""
        # Check if user has chosen a custom data directory
        data_dir_path = self.settings.value('data_directory', None, type=str)
        if data_dir_path:
            data_dir = Path(data_dir_path)
        else:
            # Default to LOCALAPPDATA or home
            base_dir = Path(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'))
            data_dir = base_dir / 'NetSpeed'
        
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / 'usage_data.db'

    def _init_db(self):
        """Initialize SQLite database and create table if it doesn't exist."""
        # Check if there's an existing database in the old/default location
        old_base_dir = Path(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'))
        old_data_dir = old_base_dir / 'NetSpeed'
        old_db_path = old_data_dir / 'usage_data.db'
        
        # If user has chosen a new directory and old DB exists, move it
        data_dir_path = self.settings.value('data_directory', None, type=str)
        if data_dir_path and old_db_path.exists() and old_db_path != self.db_path:
            # Create new directory if needed
            Path(data_dir_path).mkdir(parents=True, exist_ok=True)
            # Move the DB file
            import shutil
            shutil.move(str(old_db_path), str(self.db_path))
        
        with self.usage_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    downloaded INTEGER NOT NULL,
                    uploaded INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    month TEXT NOT NULL,
                    hour TEXT NOT NULL,
                    minute TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()

    def _load_today_data(self):
        """Load today's data from persistent storage, reset if date changed."""
        saved_date = self.settings.value('data_date', None)
        today_date_str = datetime.date.today().isoformat()
        
        if saved_date == today_date_str:
            # Load from settings
            self.today_rx = self.settings.value('today_rx', 0, type=int)
            self.today_tx = self.settings.value('today_tx', 0, type=int)
        else:
            # Reset for new day
            self.today_rx = 0
            self.today_tx = 0
            self.settings.setValue('data_date', today_date_str)
            self.settings.setValue('today_rx', 0)
            self.settings.setValue('today_tx', 0)

    def log_current_sample(self):
        """Public wrapper to log the current network usage sample.
        It reads the current counters, computes deltas, updates daily totals,
        and writes a row to the SQLite database.
        """
        # Calculate current usage since last sample
        current = psutil.net_io_counters()
        downloaded = current.bytes_recv - self.last.bytes_recv
        uploaded = current.bytes_sent - self.last.bytes_sent
        total = downloaded + uploaded
        # Update last snapshot
        self.last = current
        # Update daily counters
        self.today_rx += downloaded
        self.today_tx += uploaded
        self._save_today_data()
        # Log to database
        self._log_usage_sample(downloaded, uploaded, total)
        return downloaded, uploaded, total

    def _save_today_data(self):
        """Save today's data to persistent storage."""
        self.settings.setValue('today_rx', self.today_rx)
        self.settings.setValue('today_tx', self.today_tx)

    def _log_usage_sample(self, downloaded, uploaded, total):
        """Append the latest usage sample to the SQLite database."""
        now = datetime.datetime.now()
        with self.usage_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usage (timestamp, downloaded, uploaded, total, date, month, hour, minute)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.isoformat(timespec='seconds'),
                int(downloaded),
                int(uploaded),
                int(total),
                now.strftime('%Y-%m-%d'),
                now.strftime('%Y-%m'),
                now.strftime('%H'),
                now.strftime('%Y-%m-%d %H:%M')
            ))
            conn.commit()
            conn.close()

    def _read_usage_rows(self):
        """Read usage rows from the SQLite database."""
        rows = []
        try:
            with self.usage_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, downloaded, uploaded, total, date, month, hour, minute
                    FROM usage
                    ORDER BY id
                ''')
                for db_row in cursor.fetchall():
                    rows.append({
                        'timestamp': db_row[0],
                        'downloaded': db_row[1],
                        'uploaded': db_row[2],
                        'total': db_row[3],
                        'date': db_row[4],
                        'month': db_row[5],
                        'hour': db_row[6],
                        'minute': db_row[7]
                    })
                conn.close()
        except Exception as e:
            print(f"Error reading usage log: {e}")
        return rows

    def reset_usage(self):
        """Reset daily usage counters and persist reset."""
        self.today_rx = 0
        self.today_tx = 0
        self.settings.setValue('data_date', datetime.date.today().isoformat())
        self._save_today_data()
        # also log a zero entry
        self._log_usage_sample(0, 0, 0)

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

    def set_bandwidth_limit(self, bytes_limit):
        """Set bandwidth limit in bytes."""
        self.bandwidth_limit = bytes_limit
        self.settings.setValue('bandwidth_limit', bytes_limit)
        
    def get_bandwidth_limit(self):
        """Get bandwidth limit in bytes."""
        return self.bandwidth_limit

    def get_daily_usage(self):
        """Return today's downloaded, uploaded, total usage, and limit details."""
        rx = int(getattr(self, 'today_rx', 0))
        tx = int(getattr(self, 'today_tx', 0))
        total = rx + tx
        limit = int(getattr(self, 'bandwidth_limit', 0))
        percent_used = (total / limit * 100) if limit else 0
        return {
            'date': datetime.date.today().isoformat(),
            'downloaded': rx,
            'uploaded': tx,
            'total': total,
            'limit': limit,
            'percent_used': percent_used,
        }

    def get_usage_log_path(self):
        """Return the persistent DB file path used by the dashboard."""
        return self.db_path

    def get_usage_dashboard_path(self):
        """Return the browser dashboard HTML file path."""
        return self.db_path.with_name('usage_dashboard.html')

    def get_usage_dashboard_data(self):
        """Aggregate usage DB data for the browser dashboard."""
        today = self.get_daily_usage()
        rows = self._read_usage_rows()
        
        yearly = defaultdict(lambda: {'downloaded': 0, 'uploaded': 0, 'total': 0})
        monthly = defaultdict(lambda: {'downloaded': 0, 'uploaded': 0, 'total': 0})
        daily = defaultdict(lambda: {'downloaded': 0, 'uploaded': 0, 'total': 0})
        hourly = defaultdict(lambda: {'downloaded': 0, 'uploaded': 0, 'total': 0})
        minutely = defaultdict(lambda: {'downloaded': 0, 'uploaded': 0, 'total': 0})
        
        for row in rows:
            downloaded = row['downloaded']
            uploaded = row['uploaded']
            total = downloaded + uploaded
            year = row.get('month') or row['timestamp'][:4]  # Extract year (YYYY)
            month = row.get('month') or row['timestamp'][:7]
            date = row.get('date') or row['timestamp'][:10]
            hour = row.get('hour') or row['timestamp'][11:13]
            minute = row.get('minute') or row['timestamp'][:16]
            
            yearly[year]['downloaded'] += downloaded
            yearly[year]['uploaded'] += uploaded
            yearly[year]['total'] += total
            
            monthly[month]['downloaded'] += downloaded
            monthly[month]['uploaded'] += uploaded
            monthly[month]['total'] += total
            
            daily[date]['downloaded'] += downloaded
            daily[date]['uploaded'] += uploaded
            daily[date]['total'] += total
            
            hourly[f'{date} {hour}:00']['downloaded'] += downloaded
            hourly[f'{date} {hour}:00']['uploaded'] += uploaded
            hourly[f'{date} {hour}:00']['total'] += total
            
            minutely[minute]['downloaded'] += downloaded
            minutely[minute]['uploaded'] += uploaded
            minutely[minute]['total'] += total
        
        def to_items(data):
            return [
                {'label': label, **values}
                for label, values in data.items()
            ]
        
        return {
            'today': today,
            'yearly': sorted(to_items(yearly), key=lambda item: item['label'])[-30:],
            'monthly': sorted(to_items(monthly), key=lambda item: item['label'])[-30:],
            'daily': sorted(to_items(daily), key=lambda item: item['label'])[-30:],
            'hourly': sorted(to_items(hourly), key=lambda item: item['label'])[-30:],
            'minute': sorted(to_items(minutely), key=lambda item: item['label'])[-30:],
            'latest': rows[-30:],
            'records_count': len(rows),
            'log_path': str(self.db_path),
            'generated_at': datetime.datetime.now().isoformat(timespec='seconds')
        }

    def _is_fullscreen(self):
        """Cross-platform fullscreen detection."""
        if sys.platform == "win32":
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
        else:
            # For macOS and Linux, skip fullscreen detection for now
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
            self._log_usage_sample(dl, ul, total)
            fullscreen = self._is_fullscreen()
            return dl, ul, total, self.bandwidth_limit, fullscreen
        except Exception as e:
            print(f"Error retrieving network data: {e}")
            return 0, 0, self.today_rx + self.today_tx, self.bandwidth_limit, False
