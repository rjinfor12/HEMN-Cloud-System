import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)
sftp = client.open_sftp()

def download(remote, local):
    print(f"Downloading {remote} to {local}...")
    sftp.get(remote, local)

try:
    download("/var/www/hemn_cloud/HEMN_Cloud_Server.py", "vps_server_code.txt")
    download("/var/www/hemn_cloud/index_vps.html", "vps_index_vps.txt")
except Exception as e:
    print(f"Error: {e}")

sftp.close()
client.close()
