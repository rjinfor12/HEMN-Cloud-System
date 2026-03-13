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

    print("Resetting failed state...")
    client.exec_command('systemctl reset-failed hemn_cloud.service')
    
    print("Starting service...")
    client.exec_command('systemctl start hemn_cloud.service')
    
    time.sleep(5)
    
    print("--- Final Service Status ---")
    stdin, stdout, stderr = client.exec_command('systemctl status hemn_cloud.service')
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()
    print("Repair process finished!")
except Exception as e:
    print(f"Error: {e}")
