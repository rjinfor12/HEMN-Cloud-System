import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

def upload_dir(sftp, local_dir, remote_dir):
    if not os.path.exists(local_dir): return
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + '/' + item
        if os.path.isfile(local_path):
            print(f"Uploading {item}...")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            upload_dir(sftp, local_path, remote_path)

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)

    sftp = client.open_sftp()
    
    # Sync static folder
    local_static = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static'
    remote_static = '/var/www/hemn_cloud/static'
    upload_dir(sftp, local_static, remote_static)
    
    # Sync backend server + engine
    local_server = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\HEMN_Cloud_Server.py'
    remote_server = '/var/www/hemn_cloud/HEMN_Cloud_Server.py'
    print(f"Uploading HEMN_Cloud_Server.py...")
    sftp.put(local_server, remote_server)

    local_engine = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py'
    remote_engine = '/var/www/hemn_cloud/cloud_engine.py'
    print(f"Uploading cloud_engine.py...")
    sftp.put(local_engine, remote_engine)
    
    print("Restarting service...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    sftp.close()
    client.close()
    print("Full static sync complete!")
except Exception as e:
    print(f"Error during sync: {e}")
