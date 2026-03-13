import paramiko
import time

host = '129.121.45.136'
port = 22022
user = 'root'

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password='ChangeMe123!')

    print("Installing requests...")
    stdin, stdout, stderr = client.exec_command('/var/www/hemn_cloud/venv/bin/pip install requests')
    print(stdout.read().decode())
    print(stderr.read().decode())

    print("Restarting service...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    time.sleep(3)
    
    print("--- New Service Status ---")
    stdin, stdout, stderr = client.exec_command('systemctl status hemn_cloud.service')
    print(stdout.read().decode())

    client.close()
    print("Fix complete!")
except Exception as e:
    print(f"Error: {e}")
