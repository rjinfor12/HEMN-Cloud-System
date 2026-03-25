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
local_path = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\admin_monitor_vps.html'
sftp.get('/var/www/hemn_cloud/static/admin_monitor.html', local_path)
sftp.close()
client.close()
print(f"Downloaded to {local_path}")
