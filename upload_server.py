import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def upload_server():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # Upload HEMN_Cloud_Server.py
        sftp.put('HEMN_Cloud_Server.py', '/var/www/hemn_cloud/HEMN_Cloud_Server.py')
        print("HEMN_Cloud_Server.py uploaded.")
        
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("System restarted.")
    finally:
        client.close()

if __name__ == "__main__":
    upload_server()
