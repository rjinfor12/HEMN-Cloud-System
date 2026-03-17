import paramiko
import os

def upload_and_restart():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        sftp = client.open_sftp()
        
        # Files to upload
        files = ['cloud_engine.py', 'cloud_engine_vps.py']
        for f in files:
            local_path = os.path.join(r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis', f)
            remote_path = f'/var/www/hemn_cloud/{f}'
            print(f"Uploading {f}...")
            sftp.put(local_path, remote_path)
            
        sftp.close()
        
        print("--- Restarting hemn_cloud.service ---")
        client.exec_command("systemctl restart hemn_cloud.service")
        
        print("Done.")
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    upload_and_restart()
