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

print("--- BUSCANDO 'V1.0.3' NO VPS ---")
print(run("grep -r 'V1.0.3' /var/www/hemn_cloud/"))

print("\n--- BUSCANDO 'UIFIX-GOLD' NO VPS ---")
print(run("grep -r 'UIFIX-GOLD' /var/www/hemn_cloud/"))

print("\n--- VERIFICANDO ARQUIVOS NO DIRETORIO RAIZ ---")
print(run("ls -lh /var/www/hemn_cloud/"))

client.close()
