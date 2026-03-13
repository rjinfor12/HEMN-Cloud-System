import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def download_latest():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        uploads = '/var/www/hemn_cloud/static/uploads'
        files = sftp.listdir(uploads)
        results = [f for f in files if f.startswith('Enriquecido_')]
        results.sort()
        if results:
            latest = os.path.join(uploads, results[-1])
            sftp.get(latest, 'final_batch_result.xlsx')
            print(f"Downloaded {results[-1]}")
        else:
            print("No results found.")
        sftp.close()
    finally:
        client.close()

if __name__ == "__main__":
    download_latest()
