import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    remote_file = '/var/www/hemn_cloud/static/index.html'
    print(f"Reading {remote_file}...")
    
    stdin, stdout, stderr = client.exec_command(f'grep -C 5 "BRISANET" {remote_file}')
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if output:
        print("Found BRISANET in remote file:")
        print(output)
    else:
        print("BRISANET NOT FOUND in remote file.")
    
    if error:
        print("Error during grep:", error)

    client.close()
except Exception as e:
    print(f"Error checking remote file: {e}")
