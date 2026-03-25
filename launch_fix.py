import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
local_path = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\fix_ingest_missing_march_2026.py'
remote_path = '/var/www/hemn_cloud/fix_ingest_missing_march_2026.py'

sftp.put(local_path, remote_path)
sftp.close()

# Run in background using nohup
# We want it to keep running even if we disconnect
cmd = f'nohup /var/www/hemn_cloud/venv/bin/python3 {remote_path} > /var/www/hemn_cloud/fix_ingest.out 2>&1 &'
client.exec_command(cmd)

client.close()
print("Fix script launched in background on VPS.")
