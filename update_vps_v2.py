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
    
    sftp = client.open_sftp()
    
    # Create local temp script
    with open("temp_vps_fix.py", "w") as f:
        f.write("""
import sqlite3
DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"
conn = sqlite3.connect(DB_PATH)
conn.execute("UPDATE users SET role='CLINICAS', valor_mensal=1099.0, vencimento_dia=10, password='hemn123' WHERE username='testuser' COLLATE NOCASE")
conn.commit()
print('VPS SUCCESS: testuser updated to CLINICAS with password hemn123')
conn.close()
""")
    
    sftp.put("temp_vps_fix.py", "/tmp/temp_vps_fix.py")
    sftp.close()
    
    print("Running remote script...")
    stdin, stdout, stderr = client.exec_command("python3 /tmp/temp_vps_fix.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    client.exec_command("rm /tmp/temp_vps_fix.py")
    client.close()
    os.remove("temp_vps_fix.py")

if __name__ == "__main__":
    update_remote_user()
