import paramiko, os, sys

import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

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
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='ignore')

print('=== RESOURCE USAGE (CPU/RAM) ===')
print(run('top -bn1 | head -n 15'))

print('\n=== CHECKING LATEST LOGS FOR POLLING ===')
# Look for /tasks/{uuid} GET requests in the last 100 lines of console/uvicorn logs
# On this VPS, we might need to check journalctl or just the uvicorn output if piped
print(run('journalctl -u hemn_cloud --since "1 minute ago" | grep "GET /tasks/" | grep -v "/active" | tail -n 10'))

print('\n=== VERIFYING NUMPY IN VENV ===')
print(run('/var/www/hemn_cloud/venv/bin/python3 -c "import numpy; print(\'NumPy OK\')"'))

print('\n=== CHECKING INDEX.HTML OPTIMIZATION ===')
print(run('grep "pollTasks" /var/www/hemn_cloud/index.html -A 5 | grep "visibilityState"'))

client.close()
