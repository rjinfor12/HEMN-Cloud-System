import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

files_to_sync = [
    ('static/index.html', '/var/www/hemn_cloud/static/index.html'),
    ('index.html', '/var/www/hemn_cloud/index.html'),
    ('index_vps.html', '/var/www/hemn_cloud/index_vps.html'),
    ('static/design-system.css', '/var/www/hemn_cloud/static/design-system.css')
]

try:
    print(f"Connecting to {host}:{port} via key...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)

    sftp = client.open_sftp()
    
    base_local = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis'
    
    for local_rel, remote_abs in files_to_sync:
        local_abs = os.path.join(base_local, local_rel.replace('/', os.sep))
        print(f"Uploading {local_rel} -> {remote_abs}...")
        sftp.put(local_abs, remote_abs)
    
    print("Restarting hemn_cloud.service to ensure changes are picked up...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    sftp.close()
    client.close()
    print("=== DEPLOY PREMIUM LOGO SUCCESSFUL ===")
except Exception as e:
    print(f"Error during deployment: {e}")
