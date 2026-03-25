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
    return stdout.read().decode() + stderr.read().decode()

print("--- FILES IN /var/www/hemn_cloud/ ---")
print(run("ls -lh /var/www/hemn_cloud/"))

print("\n--- APP_DIR FROM PYTHON SCRIPT ---")
# Tenta descobrir o APP_DIR real rodando um comando python na vps
print(run("python3 -c 'import os; print(os.path.dirname(os.path.abspath(\"/var/www/hemn_cloud/HEMN_Cloud_Server.py\")))'"))

client.close()
