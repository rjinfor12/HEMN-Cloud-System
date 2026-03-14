import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

files_to_deploy = [
    (r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\index.html', '/var/www/hemn_cloud/static/index.html'),
    (r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html', '/var/www/hemn_cloud/index_vps.html'),
    (r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py', '/var/www/hemn_cloud/cloud_engine.py')
]

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    sftp = client.open_sftp()
    
    for local, remote in files_to_deploy:
        print(f"Uploading {local} to {remote}...")
        sftp.put(local, remote)
    
    sftp.close()
    
    print("Restarting hemn_cloud service...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    print("Restarting nginx just in case...")
    client.exec_command('systemctl restart nginx')
    
    client.close()
    print("Deployment completed successfully!")
except Exception as e:
    print(f"Error during deployment: {e}")
