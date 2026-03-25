import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- TIMESTAMPS IN /var/www/hemn_cloud/db_chunks ---")
cmd = 'ls -lt /var/www/hemn_cloud/db_chunks | head -n 20'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- TABLES USING SQLITE ENGINE ---")
cmd = 'clickhouse-client -q "SELECT database, name, engine_full FROM system.tables WHERE engine LIKE \'%SQLite%\'"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- CHECKING IF ANY PROCESS IS USING THESE FILES ---")
cmd = 'lsof +D /var/www/hemn_cloud/db_chunks'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
