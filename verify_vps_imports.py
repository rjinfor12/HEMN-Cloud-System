import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print("--- IMPORTS IN HEMN_Cloud_Server.py ---")
print(run("grep 'import cloud_engine' /var/www/hemn_cloud/HEMN_Cloud_Server.py"))

print("\n--- VERSION OF index_vps.html ---")
print(run("grep -c 'db-version-row' /var/www/hemn_cloud/index_vps.html"))

client.close()
