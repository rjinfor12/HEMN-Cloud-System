import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def upload_engine():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # Upload cloud_engine.py
        sftp.put('cloud_engine_to_fix_v2.py', '/var/www/hemn_cloud/cloud_engine.py')
        print("cloud_engine.py uploaded.")
        
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("System restarted.")
    finally:
        client.close()

if __name__ == "__main__":
    upload_engine()
