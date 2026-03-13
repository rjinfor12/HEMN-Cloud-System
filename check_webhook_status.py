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
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print('=== STATUS DO SERVICO ===')
print(run('systemctl is-active hemn_cloud.service'))

print('=== TESTE WEBHOOK ===')
payload = '{"event":"PING","payment":{}}'
r = run(f"curl -s -X POST http://127.0.0.1:8000/webhook/asaas -H 'Content-Type: application/json' -d '{payload}'")
print(r)

print('=== TAIL DO WEBHOOK LOG ===')
print(run('tail -20 /var/www/hemn_cloud/webhook_asaas.log 2>/dev/null || echo "Log nao existe"'))

client.close()
