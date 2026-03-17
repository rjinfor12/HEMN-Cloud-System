import paramiko
import os

def deploy_ui():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        sftp = client.open_sftp()
        
        local_index_vps = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html'
        
        # Upload to both names for safety
        print("Uploading index_vps.html to /var/www/hemn_cloud/index.html...")
        sftp.put(local_index_vps, '/var/www/hemn_cloud/index.html')
        
        print("Uploading index_vps.html to /var/www/hemn_cloud/index_vps.html...")
        sftp.put(local_index_vps, '/var/www/hemn_cloud/index_vps.html')
            
        sftp.close()
        
        print("--- Restarting hemn_cloud.service ---")
        client.exec_command("systemctl restart hemn_cloud.service")
        
        print("Done.")
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy_ui()
