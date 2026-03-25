import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

files_to_upload = [
    "HEMN_Cloud_Server.py",
    "cloud_engine.py",
    "index_vps.html",
    "vps_ingest_march_2026.py"
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
for f in files_to_upload:
    print(f"Uploading {f}...")
    sftp.put(f, f"/var/www/hemn_cloud/{f}")
sftp.close()

print("Restarting service...")
client.exec_command("systemctl restart hemn_cloud")
client.close()
print("Sync finished.")
