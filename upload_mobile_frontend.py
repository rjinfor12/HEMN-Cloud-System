import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def upload_frontend():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # Upload index.html
        sftp.put('vps_index.html', '/var/www/hemn_cloud/static/index.html')
        print("index.html uploaded.")
        
        # Upload design-system.css
        sftp.put('vps_design-system.css', '/var/www/hemn_cloud/static/design-system.css')
        print("design-system.css uploaded.")
        
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("System restarted.")
    finally:
        client.close()

if __name__ == "__main__":
    upload_frontend()
