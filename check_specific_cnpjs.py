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

cnpjs = ['24653482', '23889950', '27844352', '21867599']
cnpjs_str = ', '.join([f"'{c}'" for c in cnpjs])

print('=== VERIFICANDO CNPJS ESPECÍFICOS NO CLICKHOUSE ===')
q = f"SELECT cnpj_basico, razao_social, natureza_juridica FROM hemn.empresas WHERE cnpj_basico IN ({cnpjs_str})"
print(run(f"clickhouse-client --query \"{q}\""))

client.close()
