import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

cmd = 'clickhouse-client -q "SHOW CREATE TABLE hemn_update_tmp.empresas"'
stdin, stdout, stderr = client.exec_command(cmd)
print("CREATE TABLE RESULT:")
print(stdout.read().decode())

err = stderr.read().decode()
if err: print(f"ERROR: {err}")

client.close()
