import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def restore_admin():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {hostname}...")
    client.connect(hostname, port=port, username=username, pkey=key)
    
    sftp = client.open_sftp()
    
    # Create local temp script to restore admin
    with open("restore_admin.py", "w") as f:
        f.write("""
import sqlite3
DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"
conn = sqlite3.connect(DB_PATH)
conn.execute("UPDATE users SET role='ADMIN', password='admin123', valor_mensal=0.0 WHERE username='admin' COLLATE NOCASE")
conn.commit()
print('VPS SUCCESS: Admin restored to role=ADMIN and password=admin123')
conn.close()
""")
    
    sftp.put("restore_admin.py", "/tmp/restore_admin.py")
    sftp.close()
    
    print("Running remote script...")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/restore_admin.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.exec_command("rm /tmp/restore_admin.py")
    client.close()
    os.remove("restore_admin.py")

if __name__ == "__main__":
    restore_admin()
