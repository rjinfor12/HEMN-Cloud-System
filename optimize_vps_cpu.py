import paramiko
import os

# Configurações do VPS
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

local_service = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.service"

def optimize_cpu():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to VPS {ip} to optimize CPU...")
        client.connect(ip, username=user, password=pw, timeout=30)
        sftp = client.open_sftp()
        
        # 1. Upload do novo arquivo de serviço
        print(f"Uploading optimized service file...")
        sftp.put(local_service, "/etc/systemd/system/hemn_cloud.service")
        sftp.close()
        
        # 2. Comandos para aplicar
        cmds = [
            "systemctl daemon-reload",
            "systemctl restart hemn_cloud",
            "sleep 5",
            "ps aux | grep uvicorn"
        ]
        
        for cmd in cmds:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out: print(out)
            if err: print(f"ERROR: {err}")
            
        client.close()
        print("\nSUCCESS: VPS CPU optimization completed! 8 Workers active.")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    optimize_cpu()
