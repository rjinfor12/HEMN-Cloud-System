import paramiko
import os
import time

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

url = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9/download?path=%2F2026-03&files=Empresas0.zip"
headers = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
output_path = "/var/www/hemn_cloud/downloads/debug_test.zip"

print(f"--- DEBUG DOWNLOAD: {url} ---")
cmd = f'curl -H "{headers}" -L -o {output_path} "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
# Wait for completion (curl is synchronous here)
stdout.read()

print("\n--- FILE TYPE CHECK ---")
cmd = f'file {output_path}'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

print("\n--- HEAD CHECK ---")
cmd = f'head -n 5 {output_path}'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
