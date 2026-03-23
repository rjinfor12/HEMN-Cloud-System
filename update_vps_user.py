import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def update_remote_user():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {hostname}...")
    client.connect(hostname, port=port, username=username, pkey=key)
    
    # Python script to run on VPS
    remote_py = """
import sqlite3
DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"
conn = sqlite3.connect(DB_PATH)
conn.execute("UPDATE users SET role='CLINICAS', valor_mensal=1099.0, vencimento_dia=10, password='hemn123' WHERE username='admin' COLLATE NOCASE")
conn.commit()
print('VPS: Admin updated to CLINICAS with password hemn123')
conn.close()
"""
    # Escaping for shell
    cmd = f"python3 -c {repr(remote_py)}"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.close()

if __name__ == "__main__":
    update_remote_user()
