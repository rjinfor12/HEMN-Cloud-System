import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_vps_files():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Listing /var/www/hemn_cloud/storage/results ---")
    stdin, stdout, stderr = client.exec_command("ls -lh /var/www/hemn_cloud/storage/results")
    print(stdout.read().decode())
    
    print("\n--- Checking for AUTO-SYNC in logs ---")
    stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 300 --no-pager")
    logs = stdout.read().decode()
    for line in logs.split('\n'):
        if "[AUTO-SYNC]" in line or "Ingest" in line:
            print(line)
            
    client.close()

if __name__ == "__main__":
    check_vps_files()
