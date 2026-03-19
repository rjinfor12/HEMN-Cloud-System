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

print("=== REVERTENDO VPS PARA 3dd22bd ===")
# Note: Since I force-pushed to GitHub, a simple pull might not work on VPS if it has local changes.
# Best is git fetch + reset hard on VPS too.
print(run("cd /var/www/hemn_cloud && git fetch --all && git reset --hard 3dd22bd"))

# Reiniciar
run("systemctl restart hemn_cloud.service")

client.close()
