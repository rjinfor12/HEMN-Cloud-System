import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def verify_remote_html():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    # Check for the lock icon in index_vps.html
    stdin, stdout, stderr = client.exec_command("grep -C 5 'fa-lock' /var/www/hemn_cloud/static/index_vps.html")
    print("--- Remote index_vps.html (Lock Icon context) ---")
    print(stdout.read().decode('utf-8'))
    
    # Check user-profile section
    stdin, stdout, stderr = client.exec_command("grep -A 15 'user-profile' /var/www/hemn_cloud/static/index_vps.html")
    print("\n--- Remote index_vps.html (user-profile section) ---")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    verify_remote_html()
