import paramiko
import os

old_ip = "129.121.45.136"
old_port = 22022
old_user = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_old_stats():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(old_ip, port=old_port, username=old_user, pkey=key)
    
    print("--- Disk Usage Old VPS ---")
    commands = [
        "du -sh /var/lib/clickhouse",
        "du -sh /var/www/hemn_cloud/hemn_cloud.db",
        "du -sh /var/www/hemn_cloud/storage",
        "ls -l /var/www/hemn_cloud/HEMN_Cloud_Server.py"
    ]
    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"{cmd}: {stdout.read().decode().strip()}")
        
    client.close()

if __name__ == "__main__":
    check_old_stats()
