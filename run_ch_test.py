import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_test():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        sftp.put('test_ch_speed.py', '/root/test_ch_speed.py')
        sftp.close()
        
        stdin, stdout, stderr = client.exec_command('python3 /root/test_ch_speed.py')
        print(stdout.read().decode())
        print(stderr.read().decode())
        
    finally:
        client.close()

if __name__ == "__main__":
    run_test()
