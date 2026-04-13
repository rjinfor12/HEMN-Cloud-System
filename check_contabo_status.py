import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def check_contabo_status():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    cmds = [
        "ls -d /var/www/hemn_cloud/venv",
        "which clickhouse-server",
        "systemctl is-active clickhouse-server"
    ]
    for cmd in cmds:
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"Checking {cmd}: {stdout.read().decode().strip()}")
        
    client.close()

if __name__ == "__main__":
    check_contabo_status()
