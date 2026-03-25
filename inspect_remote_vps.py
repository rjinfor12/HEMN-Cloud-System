import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

def download_remote(client, remote_path, local_path):
    print(f"Downloading {remote_path} to {local_path}...")
    sftp = client.open_sftp()
    try:
        sftp.get(remote_path, local_path)
        print("Done.")
    except Exception as e:
        print(f"Error downloading {remote_path}: {e}")
    finally:
        sftp.close()

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    download_remote(client, '/var/www/hemn_cloud/index_vps.html', 'c:/Users/Junior T.I/.gemini/antigravity/scratch/data_analysis/remote_index_vps.html')
    download_remote(client, '/var/www/hemn_cloud/HEMN_Cloud_Server.py', 'c:/Users/Junior T.I/.gemini/antigravity/scratch/data_analysis/remote_HEMN_Cloud_Server.py')

    client.close()
except Exception as e:
    print(f"Error: {e}")
