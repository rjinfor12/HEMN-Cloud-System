import paramiko
import os

def deploy():
    host = '86.48.17.194'
    user = 'root'
    pw = '^QP67kXax9AyuvF%'
    
    local_file = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py'
    remote_file = '/var/www/hemn_cloud/cloud_engine.py'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=pw)
        
        sftp = client.open_sftp()
        print(f"Uploading {local_file} to {remote_file}...")
        sftp.put(local_file, remote_file)
        sftp.close()
        
        print("Restarting hemn_cloud.service...")
        client.exec_command('systemctl restart hemn_cloud')
        
        print("Deployment successful.")
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy()
