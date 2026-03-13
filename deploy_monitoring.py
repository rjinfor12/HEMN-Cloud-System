import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def full_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # 1. Cloud Engine
        print("Uploading cloud_engine.py...")
        sftp.put('cloud_engine_to_fix_v2.py', '/var/www/hemn_cloud/cloud_engine.py')
        
        # 2. Cloud Server
        print("Uploading HEMN_Cloud_Server.py...")
        sftp.put('HEMN_Cloud_Server.py', '/var/www/hemn_cloud/HEMN_Cloud_Server.py')
        
        # 3. Static Files
        print("Uploading static files...")
        sftp.put('static/admin.html', '/var/www/hemn_cloud/static/admin.html')
        sftp.put('static/admin_monitor.html', '/var/www/hemn_cloud/static/admin_monitor.html')
        
        sftp.close()
        
        # Restart service
        print("Restarting system...")
        client.exec_command('systemctl restart hemn_cloud')
        print("Deployment complete!")
        
    finally:
        client.close()

if __name__ == "__main__":
    full_deploy()
