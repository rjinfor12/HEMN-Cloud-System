import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- VPS HARDWARE SPECS ---")
stdin, stdout, stderr = client.exec_command('free -m')
print("RAM (MB):")
print(stdout.read().decode())

stdin, stdout, stderr = client.exec_command('nproc')
print("CPU CORES:", stdout.read().decode().strip())

stdin, stdout, stderr = client.exec_command('lsblk')
print("\nDISK PARTITIONS:")
print(stdout.read().decode())

client.close()
