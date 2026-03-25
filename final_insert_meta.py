import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Use -q and heredoc to avoid escaping hell
cmd = """clickhouse-client -q "INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Março/2026')" """
print(f"Running: {cmd}")
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

cmd = """clickhouse-client -q "SELECT * FROM hemn._metadata" """
print(f"Running: {cmd}")
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())

client.close()
