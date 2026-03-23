import paramiko
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:/Users/Junior T.I/.ssh/id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("--- PROCESS INFO ---")
print(run("ps aux | grep HEMN_Cloud_Server"))

print("--- SERVICE FILE INFO ---")
print(run("systemctl cat hemn_cloud.service"))

client.close()
