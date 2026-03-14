import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

# Local adjusted files
local_server = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\HEMN_Cloud_Server.py"
local_engine = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
local_index = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html"

# Remote paths
remote_server = "/var/www/hemn_cloud/HEMN_Cloud_Server.py"
remote_engine = "/var/www/hemn_cloud/cloud_engine.py"
remote_index = "/var/www/hemn_cloud/static/index_vps.html"

def upload_and_restart():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {hostname}...")
    client.connect(hostname, port=port, username=username, pkey=key)
    
    sftp = client.open_sftp()
    
    print(f"Uploading server code to {remote_server}...")
    sftp.put(local_server, remote_server)
    
    print(f"Uploading engine code to {remote_engine}...")
    sftp.put(local_engine, remote_engine)
    
    print("Uploading index HTML to /var/www/hemn_cloud/static/index_vps.html...")
    sftp.put(local_index, "/var/www/hemn_cloud/static/index_vps.html")
    
    print("Uploading index HTML to /var/www/hemn_cloud/index_vps.html (Priority path)...")
    sftp.put(local_index, "/var/www/hemn_cloud/index_vps.html")

    print("Uploading CSS to /var/www/hemn_cloud/static/design-system.css...")
    sftp.put(r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\design-system.css", "/var/www/hemn_cloud/static/design-system.css")

    
    sftp.close()
    
    print("Restarting service hemn_cloud...")
    client.exec_command("systemctl restart hemn_cloud")
    
    print("Deployment complete.")
    client.close()

if __name__ == "__main__":
    upload_and_restart()
