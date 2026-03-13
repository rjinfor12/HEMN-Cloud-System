import os
import shutil
import json

def test_monitor():
    sys_stats = {"cpu": 0, "ram": 0, "disk": 0}
    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):
                    print(f"Line {i}: {line.strip()}")
                
                total = int(lines[0].split()[1])
                available = int(lines[2].split()[1]) 
                
                calc = 100 - (available / total * 100)
                print(f"Total: {total}, Available: {available}")
                print(f"Calculation: 100 - ({available} / {total} * 100) = {calc}")
                
                sys_stats["ram"] = round(calc, 1)
        
        usage = shutil.disk_usage("/")
        sys_stats["disk"] = round((usage.used / usage.total) * 100, 1)
    except Exception as e:
        print(f"Error: {e}")
        
    print(f"Final sys_stats: {sys_stats}")

if __name__ == "__main__":
    test_monitor()
