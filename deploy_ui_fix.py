import paramiko
import os

def deploy_fix():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        sftp = client.open_sftp()
        
        # Uploading to multiple potential locations used by the server
        files_to_upload = [
            (r'index_vps.html', '/var/www/hemn_cloud/index.html'),
            (r'index_vps.html', '/var/www/hemn_cloud/static/index.html'),
            (r'index_vps.html', '/var/www/hemn_cloud/index_vps.html'),
            (r'index_vps.html', '/var/www/hemn_cloud/static/index_vps.html'),
            (r'static/design-system.css', '/var/www/hemn_cloud/static/design-system.css'),
            (r'HEMN_Cloud_Server.py', '/var/www/hemn_cloud/HEMN_Cloud_Server.py')
        ]
        
        for local, remote in files_to_upload:
            if os.path.exists(local):
                print(f"Uploading {local} to {remote}...")
                sftp.put(local, remote)
            else:
                print(f"Local file not found: {local}")
                
        sftp.close()
        
        print("--- Restarting hemn_cloud.service ---")
        client.exec_command("systemctl restart hemn_cloud.service")
        
        print("Done.")
        client.close()
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    deploy_fix()
