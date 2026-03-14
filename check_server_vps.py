import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_server_code():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Checking HEMN_Cloud_Server.py for areadocliente route ---")
    stdin, stdout, stderr = client.exec_command("grep -C 5 '/areadocliente' /var/www/hemn_cloud/HEMN_Cloud_Server.py")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    check_server_code()
