import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def investigate_processes():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Detailed Process List (uvicorn) ---")
    stdin, stdout, stderr = client.exec_command("ps faux | grep uvicorn | grep -v grep")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- Listening Ports ---")
    stdin, stdout, stderr = client.exec_command("netstat -tulpn | grep 8000")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- All Service Files ---")
    stdin, stdout, stderr = client.exec_command("grep -r 'uvicorn' /etc/systemd/system/")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
 investigate_processes()
