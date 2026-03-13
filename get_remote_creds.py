import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def get_creds():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        script = """
import sqlite3
import json
conn = sqlite3.connect('/var/www/hemn_cloud/hemn_users.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password FROM users LIMIT 1')
row = cursor.fetchone()
conn.close()
if row:
    print(json.dumps({'user': row[0], 'pass': row[1]}))
else:
    print('None')
"""
        with sftp.open('/tmp/get_creds.py', 'w') as f:
            f.write(script)
            
        stdin, stdout, stderr = client.exec_command('python3 /tmp/get_creds.py')
        res = stdout.read().decode().strip()
        print(res)
    finally:
        client.close()

if __name__ == "__main__":
    get_creds()
