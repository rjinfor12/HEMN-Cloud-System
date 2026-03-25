import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- SAMPLE FROM hemn.socios ---")
cmd = 'clickhouse-client -q "SELECT cnpj, cnpj_basico, nome_socio, socio_chave FROM hemn.socios LIMIT 5"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- SAMPLE FROM hemn.estabelecimento ---")
cmd = 'clickhouse-client -q "SELECT cnpj_basico, cnpj_ordem, cnpj_dv, cnpj FROM hemn.estabelecimento LIMIT 5"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
