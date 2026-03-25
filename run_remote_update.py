import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

sftp = client.open_sftp()
local_file = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\update_hemn_clickhouse.py'
remote_file = '/tmp/update_hemn_clickhouse.py'

print(f"Uploading {local_file} to {remote_file}...")
sftp.put(local_file, remote_file)
sftp.close()

print("Running the update script on VPS...")
cmd = "/var/www/hemn_cloud/venv/bin/python " + remote_file
stdin, stdout, stderr = client.exec_command(cmd)

# Monitor output
for line in stdout:
    print(line.strip())

err = stderr.read().decode('utf-8')
if err:
    print("ERRORS:", err)

client.close()
