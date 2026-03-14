import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def compare_html_files():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    paths = [
        "/var/www/hemn_cloud/index_vps.html",
        "/var/www/hemn_cloud/static/index_vps.html"
    ]
    
    for path in paths:
        print(f"\n--- Checking {path} ---")
        stdin, stdout, stderr = client.exec_command(f"grep 'fa-lock' {path}")
        output = stdout.read().decode('utf-8')
        if "fa-lock" in output:
            print("FOUND fa-lock (New Version)")
        else:
            print("NOT FOUND fa-lock (Old Version)")
            
    client.close()

if __name__ == "__main__":
    compare_html_files()
