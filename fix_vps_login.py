import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

print(f"Connecting to {host}:{port}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=port, username=user, password=password, timeout=10)
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

print("Uploading FIXED index_vps.html to VPS...")
sftp = client.open_sftp()
sftp.put("index_vps.html", "/var/www/hemn_cloud/index_vps.html")
sftp.close()

print("Restarting hemn_cloud service...")
stdin, stdout, stderr = client.exec_command('systemctl restart hemn_cloud.service')
exit_status = stdout.channel.recv_exit_status()
if exit_status == 0:
    print("Service restarted successfully!")
else:
    print(f"Error restarting service. Exit status: {exit_status}")
    print("ERR:", stderr.read().decode())

client.close()
print("Fix applied. Please check the website.")
