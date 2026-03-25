import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

files_to_upload = [
    ("HEMN_Cloud_Server.py", "/var/www/hemn_cloud/HEMN_Cloud_Server.py"),
    ("cloud_engine.py", "/var/www/hemn_cloud/cloud_engine.py"),
    ("index_vps.html", "/var/www/hemn_cloud/index_vps.html"),
    ("remote_index_vps.html", "/var/www/hemn_cloud/remote_index_vps.html"),
    ("vps_design-system.css", "/var/www/hemn_cloud/vps_design-system.css"),
    ("static/design-system.css", "/var/www/hemn_cloud/static/design-system.css")
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
for local_f, remote_f in files_to_upload:
    print(f"Uploading {local_f} to {remote_f}...")
    # Ensure remote directory exists (simple check for static)
    if "/" in remote_f:
        remote_dir = "/".join(remote_f.split("/")[:-1])
        try:
            sftp.mkdir(remote_dir)
        except:
            pass
    sftp.put(local_f, remote_f)
sftp.close()

print("Restarting service...")
client.exec_command("systemctl restart hemn_cloud")
client.close()
print("Sync finished.")
