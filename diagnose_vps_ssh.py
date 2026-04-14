import paramiko
import os

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def diagnose_vps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        commands = [
            "ls -la /var/www/hemn_cloud/",
            "ls -la /var/www/hemn_cloud/static/",
            "grep 'app.mount' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py",
            "cat /etc/nginx/sites-enabled/hemn",
            "systemctl status hemn_cloud"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out: print(out)
            if err: print(f"ERROR: {err}")
            
        client.close()
    except Exception as e:
        print(f"FAILED TO CONNECT: {e}")

if __name__ == "__main__":
    diagnose_vps()
