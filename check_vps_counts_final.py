import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def get_count(table):
    cmd = f"clickhouse-client -q 'SELECT count() FROM hemn_update_tmp.{table}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    return res

print(f"estabelecimento: {get_count('estabelecimento')}")
print(f"empresas: {get_count('empresas')}")
print(f"socios: {get_count('socios')}")
print(f"simples: {get_count('simples')}")

client.close()
