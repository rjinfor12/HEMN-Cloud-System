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
    
    local_file = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py'
    remote_file = '/var/www/hemn_cloud/cloud_engine.py'
    
    print(f"Uploading {local_file} to {remote_file}...")
    sftp.put(local_file, remote_file)
    
    print("Restarting service just in case...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    sftp.close()
    client.close()
    print("Backend deployment completed successfully!")
except Exception as e:
    print(f"Error during deployment: {e}")
