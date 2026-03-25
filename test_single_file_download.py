import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- TESTING INDIVIDUAL FILE DOWNLOAD LINK ---")
# Direct link for a single file in the March 2026 folder
url = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9/download?path=%2F2026-03&files=Estabelecimentos0.zip"
cmd = f'curl -I -L "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
