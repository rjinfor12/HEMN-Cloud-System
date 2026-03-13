import paramiko
import os

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('129.121.45.136', port=22022, username='root', key_filename=os.path.expanduser('~/.ssh/id_rsa'))
    
    sftp = client.open_sftp()
    script = """
import sqlite3
import os
db = '/var/www/hemn_cloud/hemn_users.db'
if os.path.exists(db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT username, password FROM users LIMIT 1')
    res = cur.fetchone()
    if res:
        print(f"{res[0]}|{res[1]}")
    conn.close()
"""
    with sftp.open('/tmp/get_creds_final.py', 'w') as f:
        f.write(script)
    
    stdin, stdout, stderr = client.exec_command('python3 /tmp/get_creds_final.py')
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    run()
