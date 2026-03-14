import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_service_file():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Systemd Service File (/etc/systemd/system/hemn_cloud.service) ---")
    stdin, stdout, stderr = client.exec_command("cat /etc/systemd/system/hemn_cloud.service")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- Current Directory of Running Process ---")
    stdin, stdout, stderr = client.exec_command("pwdx $(pgrep -f uvicorn)")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- Search for all index_vps.html files ---")
    stdin, stdout, stderr = client.exec_command("find / -name index_vps.html 2>/dev/null")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    check_service_file()
