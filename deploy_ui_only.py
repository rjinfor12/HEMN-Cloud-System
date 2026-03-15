import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    sftp = client.open_sftp()
    
    local_index = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\index.html'
    remote_index = '/var/www/hemn_cloud/static/index.html'
    
    local_vps = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html'
    remote_vps = '/var/www/hemn_cloud/index_vps.html'
    
    local_css = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\design-system.css'
    remote_css = '/var/www/hemn_cloud/static/design-system.css'
    
    print(f"Uploading {local_index} to {remote_index}...")
    sftp.put(local_index, remote_index)
    
    print(f"Uploading {local_vps} to {remote_vps}...")
    sftp.put(local_vps, remote_vps)
    
    print(f"Uploading {local_css} to {remote_css}...")
    sftp.put(local_css, remote_css)
    
    print("Restarting service just in case...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    sftp.close()
    client.close()
    print("UI deployment completed successfully!")
except Exception as e:
    print(f"Error during deployment: {e}")
