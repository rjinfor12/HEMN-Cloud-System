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
        
        local_server = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\HEMN_Cloud_Server.py'
        remote_server = '/var/www/hemn_cloud/HEMN_Cloud_Server.py'
        
        print(f"Uploading {local_server} to {remote_server}...")
        sftp.put(local_server, remote_server)
        sftp.close()
        
        print("--- Restarting hemn_cloud.service ---")
        client.exec_command("systemctl restart hemn_cloud.service")
        
        print("Done.")
        client.close()
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    deploy_fix()
