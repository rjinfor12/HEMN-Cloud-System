import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# Search for Rogerio and check for duplicates
query = "SELECT DISTINCT cpf, nome, dt_nascimento, uf, regiao FROM hemn.leads WHERE lower(nome) LIKE '%rogerio elias do nascimento junior%' LIMIT 10"
cmd = f"clickhouse-client --query \"{query}\""

print(f"Executing search with DISTINCT: {cmd}")
print(run(cmd))

client.close()
