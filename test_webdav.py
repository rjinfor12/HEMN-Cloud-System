import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# WebDAV public share URL:
# https://arquivos.receitafederal.gov.br/public.php/dav/
# Credentials: Share Token as username, empty password.
share_token = "YggdBLfdninEJX9"
url = "https://arquivos.receitafederal.gov.br/public.php/dav/2026-03"

print(f"--- TESTING WEBDAV PROPFIND: {url} ---")
# Depth 1 to see files inside 2026-03
cmd = f'curl -u {share_token}: -X PROPFIND -H "Depth: 1" {url}'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
