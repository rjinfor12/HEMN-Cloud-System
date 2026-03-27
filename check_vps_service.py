import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password='ChangeMe123!')

    print("--- Service Status ---")
    stdin, stdout, stderr = client.exec_command('systemctl status hemn_cloud.service')
    print(stdout.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode())
    print(stderr.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode())

    print("\n--- Recent Logs ---")
    stdin, stdout, stderr = client.exec_command('journalctl -u hemn_cloud.service -n 50')
    print(stdout.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode())

    client.close()
except Exception as e:
    print(f"Error: {e}")
