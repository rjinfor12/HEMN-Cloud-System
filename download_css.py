import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

remote_path = "/var/www/hemn_cloud/static/design-system.css"
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\design-system.css"

def download_css():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    sftp = client.open_sftp()
    print(f"Downloading {remote_path}...")
    sftp.get(remote_path, local_path)
    sftp.close()
    client.close()
    print("Download complete.")

if __name__ == "__main__":
    download_css()
