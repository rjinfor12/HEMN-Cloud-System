import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

cmd = 'clickhouse-client -q "SHOW TABLES FROM hemn_update_tmp"'
stdin, stdout, stderr = client.exec_command(cmd)
print("SHOW TABLES RESULT:")
print(stdout.read().decode())

client.close()
