import paramiko, os, sys

sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='root', key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("=== LOCALIZANDO TOKENS NO CLOUD_ENGINE.PY ===")
print("TOKEN 1 (START):")
print(run("grep -n 'PHASE 1.1' /var/www/hemn_cloud/cloud_engine.py"))
print("TOKEN 2 (END):")
print(run("grep -n 'PHASE 1.3: INTELIGÊNCIA RESIDUAL' /var/www/hemn_cloud/cloud_engine.py"))

client.close()
