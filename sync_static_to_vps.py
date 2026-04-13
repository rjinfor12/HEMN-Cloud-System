import paramiko
import os
from stat import S_ISDIR

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'
local_path = r'C:\Users\Junior T.I\.gemini\antigravity\scratch\static'
remote_path = '/var/www/hemn_cloud/static'

def sync_dir(sftp, localdir, remotedir):
    try:
        sftp.mkdir(remotedir)
    except IOError:
        pass
    
    for item in os.listdir(localdir):
        l_item = os.path.join(localdir, item)
        # Use simple slash for remote paths (Linux)
        r_item = remotedir + '/' + item
        if os.path.isfile(l_item):
            print(f"Uploading {l_item} to {r_item}")
            sftp.put(l_item, r_item)
        elif os.path.isdir(l_item):
            sync_dir(sftp, l_item, r_item)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    
    sftp = ssh.open_sftp()
    
    # Ensure remote path exists
    try:
        sftp.mkdir('/var/www/hemn_cloud')
    except: pass
    
    print(f"Starting sync from {local_path} to {remote_path}")
    sync_dir(sftp, local_path, remote_path)
    
    sftp.close()
    ssh.close()
    print("Sync complete!")
except Exception as e:
    print(f"Error: {e}")
