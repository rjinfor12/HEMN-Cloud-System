import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("--- TESTING DOWNLOAD LINK (HEAD REQUEST) ---")
# Use curl -I to check if the link is reachable and what is the content type
url = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9/download?path=%2F2026-03"
cmd = f'curl -I -L "{url}"'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())

client.close()
