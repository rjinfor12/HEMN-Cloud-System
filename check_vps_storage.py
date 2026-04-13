import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore')

print("--- Armazenamento em Pastas ---")
print(run_cmd(client, "du -sh /var/www/hemn_cloud /var/www/hemn_cloud_dev"))

print("\n--- Armazenamento ClickHouse ---")
print(run_cmd(client, 'clickhouse-client --query "SELECT database, formatReadableSize(sum(data_compressed_bytes)) FROM system.parts WHERE database IN (\'hemn\', \'hemn_dev\') GROUP BY database"'))

print("\n--- Armazenamento Total da VPS ---")
print(run_cmd(client, "df -h /"))

client.close()
