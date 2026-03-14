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

# Search in socios table
query = "SELECT cnpj, nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE lower(nome_socio) LIKE '%reginaldo moura da silva%' LIMIT 10"
cmd = f"clickhouse-client --query \"{query}\""

print(f"Executing: {cmd}")
print(run(cmd))

client.close()
