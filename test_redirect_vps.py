import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Direct WebDAV-style download URL from the redirect
url = "https://arquivos.receitafederal.gov.br/public.php/dav/files/YggdBLfdninEJX9/?accept=zip&files=Empresas0.zip"

print(f"--- TESTING DIRECT REDIRECT URL: {url} ---")
cmd = f'curl -I -L "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
