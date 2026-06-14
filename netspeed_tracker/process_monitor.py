
import psutil
import time
import threading
from collections import defaultdict
from PyQt5 import QtCore

class ProcessMonitor:
    def __init__(self):
        self.process_stats = {}  # pid: {name, last_rx, last_tx}
        self.stats_lock = threading.Lock()
        self.last_update_time = time.time()
        self.settings = QtCore.QSettings('NetSpeed', 'Overlay')
        
        # Initialize process stats
        self._init_process_stats()
    
    def _init_process_stats(self):
        """Initialize process stats by getting current connections/IO for all processes."""
        with self.stats_lock:
            self.process_stats.clear()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # For now, we'll track basic info (we'll enhance this)
                    self.process_stats[proc.info['pid']] = {
                        'name': proc.info['name'],
                        'downloaded': 0,
                        'uploaded': 0,
                        'last_check': time.time()
                    }
                except Exception:
                    pass
    
    def get_process_usage(self):
        """
        Get current per-process network usage.
        Returns a sorted list of processes by total data usage.
        """
        with self.stats_lock:
            # Convert to list and sort by total usage (download + upload)
            process_list = [
                {
                    'pid': pid,
                    'name': stats['name'],
                    'downloaded': stats['downloaded'],
                    'uploaded': stats['uploaded'],
                    'total': stats['downloaded'] + stats['uploaded']
                }
                for pid, stats in self.process_stats.items()
            ]
            return sorted(process_list, key=lambda x: x['total'], reverse=True)
    
    def refresh_process_stats(self):
        """Refresh process list and basic info (for now)."""
        with self.stats_lock:
            current_pids = set()
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    current_pids.add(pid)
                    
                    if pid not in self.process_stats:
                        self.process_stats[pid] = {
                            'name': name,
                            'downloaded': 0,
                            'uploaded': 0,
                            'last_check': time.time()
                        }
                    else:
                        # Update name in case it changed (unlikely)
                        self.process_stats[pid]['name'] = name
                        
                except Exception:
                    pass
            
            # Remove old processes that are no longer running
            pids_to_remove = []
            for pid in self.process_stats:
                if pid not in current_pids:
                    pids_to_remove.append(pid)
            for pid in pids_to_remove:
                del self.process_stats[pid]
    
    # TODO: Enhance with actual network byte tracking
    # For Windows, this requires deeper integration (ETW, WMI, or library like pyshark/npcap)
