import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def check_services():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("--- Contabo Service Status ---")
    commands = [
        "systemctl status hemn_cloud --no-pager",
        "systemctl status nginx --no-pager",
        "netstat -tuln | grep -E ':80|:8000'",
        "journalctl -u hemn_cloud -n 50 --no-pager"
    ]
    for cmd in commands:
        print(f"\n[EXEC] {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
    client.close()

if __name__ == "__main__":
    check_services()
