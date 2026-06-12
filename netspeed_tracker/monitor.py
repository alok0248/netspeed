import psutil, time, datetime

class NetMonitor:
    def __init__(self):
        self.last = psutil.net_io_counters()
        self.today_rx = 0
        self.today_tx = 0
        # start midnight reset in a daemon thread
        import threading
        threading.Thread(target=self._reset_at_midnight, daemon=True).start()

    def _reset_at_midnight(self):
        while True:
            now = datetime.datetime.now()
            # seconds until next midnight
            next_mid = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            time.sleep((next_mid - now).total_seconds())
            self.today_rx = self.today_tx = 0

    def sample(self):
        cur = psutil.net_io_counters()
        dl = cur.bytes_recv - self.last.bytes_recv
        ul = cur.bytes_sent - self.last.bytes_sent
        self.last = cur
        self.today_rx += dl
        self.today_tx += ul
        return dl, ul
