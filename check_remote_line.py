import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

cmd = "sed -n '90,95p' /var/www/hemn_cloud/cloud_engine.py"
stdin, stdout, stderr = client.exec_command(cmd)
print("Remote lines 90-95:")
print(stdout.read().decode('utf-8'))
client.close()
