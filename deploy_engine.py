import paramiko
import os

def deploy_engine():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    local_engine = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py'
    remote_engine = '/var/www/hemn_cloud/cloud_engine.py'
    
    local_html = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\index_vps.html'
    remote_html = '/var/www/hemn_cloud/index_vps.html'
    
    local_static_html = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\index.html'
    remote_static_html = '/var/www/hemn_cloud/static/index.html'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # Upload Engine
        sftp = ssh.open_sftp()
        print(f"Uploading {local_engine} to VPS...")
        sftp.put(local_engine, remote_engine)
        
        # Upload HTML
        print(f"Uploading {local_html} to VPS...")
        sftp.put(local_html, remote_html)
        
        # Upload Static HTML
        print(f"Uploading {local_static_html} to VPS...")
        try:
            sftp.put(local_static_html, remote_static_html)
        except Exception as e:
            print(f"Note: Could not upload to {remote_static_html} (might not exist): {e}")

        sftp.close()
        
        # Restart Service
        print("Restarting HEMN Service on VPS...")
        ssh.exec_command('systemctl restart hemn_cloud.service')
        
        ssh.close()
        print("Deploy successful.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    deploy_engine()
