
import psutil

def test_per_process():
    print("Testing per-process network stats...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            print(f"Process: {proc.info['name']} (PID: {proc.info['pid']})")
            # Try to get network stats for the process
            try:
                io_counters = proc.net_io_counters()
                print(f"  Network IO: {io_counters}")
            except Exception as e:
                print(f"  Could not get network stats: {e}")
        except Exception as e:
            print(f"Error accessing process: {e}")

if __name__ == "__main__":
    test_per_process()
