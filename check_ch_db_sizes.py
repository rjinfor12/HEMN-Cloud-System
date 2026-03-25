import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- CLICKHOUSE DATABASE SIZES ---")
cmd = 'clickhouse-client -q "SELECT database, formatReadableSize(sum(data_compressed_bytes)) AS compressed, formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed FROM system.parts GROUP BY database"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- TOP TABLES BY SIZE ---")
cmd = 'clickhouse-client -q "SELECT database, table, formatReadableSize(sum(data_compressed_bytes)) AS compressed FROM system.parts WHERE active GROUP BY database, table ORDER BY sum(data_compressed_bytes) DESC LIMIT 20"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
