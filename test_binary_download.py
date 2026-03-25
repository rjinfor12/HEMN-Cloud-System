import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

share_token = "YggdBLfdninEJX9"
# Trying the DAV path for the file
url = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{share_token}/2026-03/Cnaes.zip"
output_file = "/var/www/hemn_cloud/test_download.zip"

print(f"--- ATTEMPTING BINARY DOWNLOAD: {url} ---")
# -u token: (no password)
cmd = f'curl -u {share_token}: -L -o {output_file} "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
# Wait
stdout.read()

print("\n--- CHECKING FILE ---")
cmd = f'file {output_file} && ls -lh {output_file}'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
