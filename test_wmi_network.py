
import wmi

def test_wmi_network():
    print("Testing WMI for per-process network stats...")
    try:
        c = wmi.WMI()
        
        # Get network adapters
        print("Network adapters:")
        for adapter in c.Win32_NetworkAdapter():
            if adapter.NetConnectionStatus == 2:  # Connected
                print(f"  {adapter.Name}")
        
        # Try to get per-process network stats using Win32_PerfRawData_Tcpip_Tcpv4 (or similar)
        # Wait, actually, let's check Win32_Process
        print("\nProcesses:")
        for process in c.Win32_Process():
            try:
                print(f"  {process.Name} (PID: {process.ProcessId})")
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wmi_network()
