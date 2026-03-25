import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- COUNT OF POPULATED socio_chave ---")
cmd = 'clickhouse-client -q "SELECT count() FROM hemn.socios WHERE socio_chave != \'\'"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- SAMPLE OF POPULATED socio_chave ---")
cmd = 'clickhouse-client -q "SELECT cnpj_basico, nome_socio, socio_chave FROM hemn.socios WHERE socio_chave != \'\' LIMIT 5"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
