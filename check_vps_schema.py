import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- CHECKING DB SCHEMA ---")
stdin, stdout, stderr = client.exec_command('sqlite3 /var/www/hemn_cloud/hemn_cloud.db ".schema background_tasks"')
print(stdout.read().decode())
client.close()
