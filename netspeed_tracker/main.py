import sys, time, os
from PyQt5 import QtWidgets, QtCore
from .monitor import NetMonitor
from .ui import SpeedOverlay
from .tray import start_tray

# Windows-specific file locking
if sys.platform == 'win32':
    import msvcrt
    
    class SingleInstance:
        def __init__(self):
            self.lockfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'netspeed.lock')
            self.lock_file_handle = None

        def is_running(self):
            try:
                # Try to open the lock file in write mode
                self.lock_file_handle = open(self.lockfile, 'w')
                # Try to acquire an exclusive lock (non-blocking)
                try:
                    msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                    return False
                except IOError:
                    # Lock is held by another process
                    self.lock_file_handle.close()
                    return True
            except Exception:
                return False

        def release(self):
            if self.lock_file_handle:
                try:
                    msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    self.lock_file_handle.close()
                except Exception:
                    pass
                try:
                    os.unlink(self.lockfile)
                except Exception:
                    pass
else:
    import fcntl
    
    class SingleInstance:
        def __init__(self):
            self.lockfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'netspeed.lock')
            self.lock_file_handle = None

        def is_running(self):
            try:
                # Try to open the lock file in write mode
                self.lock_file_handle = open(self.lockfile, 'w')
                # Try to acquire an exclusive lock (non-blocking)
                try:
                    fcntl.flock(self.lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return False
                except IOError:
                    # Lock is held by another process
                    self.lock_file_handle.close()
                    return True
            except Exception:
                return False

        def release(self):
            if self.lock_file_handle:
                try:
                    fcntl.flock(self.lock_file_handle, fcntl.LOCK_UN)
                    self.lock_file_handle.close()
                except Exception:
                    pass
                try:
                    os.unlink(self.lockfile)
                except Exception:
                    pass

class Worker(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(float, float, float, float, bool)

    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.running = True

    def run(self):
        while self.running:
            dl, ul, total, limit, fullscreen = self.monitor.sample()
            self.update_signal.emit(dl, ul, total, limit, fullscreen)
            time.sleep(1)

def run():
    try:
        print("Starting NetSpeed...")
        
        # Check for single instance (temporarily commented out for testing)
        # single_instance = SingleInstance()
        # if single_instance.is_running():
        #     print("Another instance is already running. Exiting.")
        #     sys.exit(0)
        
        print("Creating QApplication...")
        app = QtWidgets.QApplication(sys.argv)
        print("Starting NetMonitor...")
        monitor = NetMonitor()
        print("Creating overlay...")
        overlay = SpeedOverlay(monitor)
        print("Showing overlay...")
        overlay.show()
        print("Starting tray icon...")
        start_tray(app, overlay)
        
        worker = Worker(monitor)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        
        def update_ui(dl, ul, total, limit, fullscreen):
            print(f"Update UI: dl={dl}, ul={ul}, total={total}, limit={limit}, fullscreen={fullscreen}")
            overlay.update_text(dl, ul, total, limit, fullscreen)
        
        worker.update_signal.connect(update_ui)
        thread.started.connect(worker.run)
        thread.start()
        
        # Cleanup lock on exit (temporarily commented out)
        # app.aboutToQuit.connect(single_instance.release)
        
        print("Entering app exec loop...")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    run()
