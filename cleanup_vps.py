import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def cleanup_and_restart():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("Stopping hemn_cloud service...")
    client.exec_command("systemctl stop hemn_cloud")
    
    print("Killing any remaining uvicorn processes...")
    client.exec_command("pkill -9 uvicorn")
    client.exec_command("pkill -9 python")
    
    print("Restarting hemn_cloud service...")
    client.exec_command("systemctl start hemn_cloud")
    
    print("Verifying running processes...")
    stdin, stdout, stderr = client.exec_command("pwdx $(pgrep -f uvicorn)")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    cleanup_and_restart()
