import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_nginx_config():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Nginx Configs (/etc/nginx/sites-enabled/) ---")
    stdin, stdout, stderr = client.exec_command("ls /etc/nginx/sites-enabled/")
    files = stdout.read().decode('utf-8').split()
    for f in files:
        print(f"\n--- {f} ---")
        stdin, stdout, stderr = client.exec_command(f"cat /etc/nginx/sites-enabled/{f}")
        print(stdout.read().decode('utf-8'))
    
    print("\n--- Nginx Main Config ---")
    stdin, stdout, stderr = client.exec_command("cat /etc/nginx/nginx.conf")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    check_nginx_config()
