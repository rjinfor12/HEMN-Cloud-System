import paramiko
import sys

# Hostgator info
hostgator_ip = "129.121.45.136"
hostgator_port = 22022
hostgator_user = "root"
hostgator_key_path = "C:/Users/Junior T.I/.ssh/id_rsa"

def check_progress():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        key = paramiko.RSAKey.from_private_key_file(hostgator_key_path)
        client.connect(hostgator_ip, port=hostgator_port, username=hostgator_user, pkey=key, timeout=20)
        
        print("Checking ClickHouse rsync log...")
        stdin, stdout, stderr = client.exec_command("tail -n 5 /tmp/rsync_ch.log")
        print("CH Log:", stdout.read().decode('utf-8', 'ignore'))
        
        print("Checking Storage rsync log...")
        stdin, stdout, stderr = client.exec_command("tail -n 5 /tmp/rsync_storage.log")
        print("Storage Log:", stdout.read().decode('utf-8', 'ignore'))
        
        # Check disk usage on Contabo from Hostgator point of view? No, easier to check on Contabo directly.
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_progress()
