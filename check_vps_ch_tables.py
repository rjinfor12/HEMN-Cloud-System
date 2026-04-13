import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

cmd = "clickhouse-client --query \"SELECT database, name FROM system.tables WHERE database != 'system'\""
stdin, stdout, stderr = client.exec_command(cmd)
print("--- ClickHouse Tables ---")
print(stdout.read().decode())
print("--- Errors ---")
print(stderr.read().decode())

client.close()
