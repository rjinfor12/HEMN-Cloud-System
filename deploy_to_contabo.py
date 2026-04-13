import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def deploy_to_contabo():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    sftp = client.open_sftp()
    
    # 1. Create base dirs
    print("Creating directories...")
    client.exec_command("mkdir -p /var/www/hemn_cloud/storage/results")
    
    # 2. Upload Core Files
    files = ["HEMN_Cloud_Server_VPS.py", "cloud_engine.py", "index_vps.html"]
    for f in files:
        print(f"Uploading {f}...")
        remote_path = f"/var/www/hemn_cloud/{f}"
        sftp.put(f, remote_path)
    
    # 3. Provision (Simplified)
    print("Provisioning dependencies...")
    commands = [
        "apt update && apt install -y python3-pip python3-venv sqlite3 nginx",
        "python3 -m venv /var/www/hemn_cloud/venv",
        "/var/www/hemn_cloud/venv/bin/pip install fastapi uvicorn pandas openpyxl paramiko clickhouse-driver clickhouse-connect psutil"
    ]
    for cmd in commands:
        print(f"[EXEC] {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status() # Wait for completion
        
    # 4. Pull SQLite DB from OLD VPS to LOCAL then to NEW VPS?
    # No, let's pull it directly or use local copy if we have one.
    # Actually, I'll pull from Hostgator in the next step.
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    deploy_to_contabo()
