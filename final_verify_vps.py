import requests
import json
import jwt
from datetime import datetime, timedelta

# Mocking a token check isn't easy without the secret key,
# but I'll just check if the code on the VPS is returning the right format
# by running a local script on the VPS that imports the function.

import paramiko
host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

cmd = "cd /var/www/hemn_cloud && venv/bin/python3 -c \"from cloud_engine import CloudEngine; engine = CloudEngine(); print(list(engine.get_internal_stats().keys()))\""
print(f"Running: {cmd}")
stdin, stdout, stderr = client.exec_command(cmd)
print("Keys:", stdout.read().decode())
print("Errors:", stderr.read().decode())

cmd2 = "cd /var/www/hemn_cloud && venv/bin/python3 -c \"from cloud_engine import CloudEngine; engine = CloudEngine(); stats = engine.get_internal_stats(); print('tasks type:', type(stats.get('tasks'))); print('recent count:', len(stats.get('recent_activities', [])))\""
stdin, stdout, stderr = client.exec_command(cmd2)
print("Check:", stdout.read().decode())

client.close()
