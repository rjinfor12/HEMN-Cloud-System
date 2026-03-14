import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def search_files():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Searching for HEMN_Cloud_Server.py ---")
    stdin, stdout, stderr = client.exec_command("find / -name HEMN_Cloud_Server.py 2>/dev/null")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- Searching for index_vps.html ---")
    stdin, stdout, stderr = client.exec_command("find / -name index_vps.html 2>/dev/null")
    print(stdout.read().decode('utf-8'))
    
    print("\n--- Checking for potential 'areadocliente' routes in all python files ---")
    stdin, stdout, stderr = client.exec_command("grep -rl 'areadocliente' /var/www/hemn_cloud/ /root/ 2>/dev/null")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    search_files()
