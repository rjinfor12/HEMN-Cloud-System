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
            if item.endswith(('.html', '.css', '.js', '.png', '.jpg', '.svg')):
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
    
    # 1. Sync index_vps.html to BOTH index.html and index_vps.html (Server prioritizes index_vps.html if it exists)
    local_index_vps = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html'
    remote_index = '/var/www/hemn_cloud/index.html'
    remote_index_vps = '/var/www/hemn_cloud/index_vps.html'
    
    print(f"Uploading {local_index_vps} as {remote_index} and {remote_index_vps}...")
    sftp.put(local_index_vps, remote_index)
    sftp.put(local_index_vps, remote_index_vps)
    
    # 2. Sync backend server
    backend_files = [
        ('HEMN_Cloud_Server.py', '/var/www/hemn_cloud/HEMN_Cloud_Server.py'),
        ('cloud_engine.py', '/var/www/hemn_cloud/cloud_engine.py')
    ]
    for local_name, remote_path in backend_files:
        local_path = os.path.join(r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis', local_name)
        print(f"Uploading {local_name}...")
        sftp.put(local_path, remote_path)

    # 3. Sync static folder
    local_static = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static'
    remote_static = '/var/www/hemn_cloud/static'
    print(f"Syncing static folder: {local_static} -> {remote_static}...")
    upload_dir(sftp, local_static, remote_static)
    
    # 3. Restart service to clear any potential server-side caches (though mostly frontend)
    print("Restarting service hemn_cloud.service...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    print("\nSUCCESS: DEPLOY COMPLETE!")
    print("Checkout UI and CPF/CNPJ Masking applied to VPS.")
except Exception as e:
    print(f"ERROR during deploy: {e}")
