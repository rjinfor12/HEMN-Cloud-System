import paramiko
import os
import time

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def provision_contabo():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    commands = [
        "apt update && apt install -y python3-pip python3-venv sqlite3 nginx curl gnupg2",
        "mkdir -p /var/www/hemn_cloud/storage/results",
        "python3 -m venv /var/www/hemn_cloud/venv",
        "/var/www/hemn_cloud/venv/bin/pip install fastapi uvicorn pandas openpyxl paramiko clickhouse-driver clickhouse-connect psutil",
        # Install ClickHouse (Official Repo)
        "apt-get install -y apt-transport-https ca-certificates dirmngr",
        "apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754",
        "echo 'deb https://packages.clickhouse.com/deb stable main' | tee /etc/apt/sources.list.d/clickhouse.list",
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y clickhouse-server clickhouse-client",
        "systemctl enable clickhouse-server && systemctl start clickhouse-server"
    ]
    
    for cmd in commands:
        print(f"\n[EXEC] {cmd}...")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err: print(f"[ERR] {err}")
        
    client.close()

if __name__ == "__main__":
    provision_contabo()
