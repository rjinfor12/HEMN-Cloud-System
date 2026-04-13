import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def diagnose_live():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- LIVE LOGS (Last 50 lines) ---")
    stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 50 --no-pager")
    print(stdout.read().decode())
    
    print("\n--- Check running process command line ---")
    stdin, stdout, stderr = client.exec_command("ps aux | grep HEMN_Cloud_Server")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    diagnose_live()
