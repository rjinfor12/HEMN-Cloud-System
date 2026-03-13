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

print('=== TESTE PREFIXO /areadocliente/ ===')
r = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/areadocliente/")
print(f"Index path result: {r}")

print('=== TESTE LOGIN ENDPOINT (PREFIXADO) ===')
# Deve retornar 405 Method Not Allowed ou 422 se dermos GET em um POST, mas deve ser 200/401 se for POST
r = run("curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/areadocliente/login")
print(f"Login path result: {r}")

print('=== TESTE WEBHOOK ENDPOINT (PREFIXADO) ===')
r = run("curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/areadocliente/webhook/asaas -H 'Content-Type: application/json' -d '{\"event\":\"PING\"}'")
print(f"Webhook path result: {r}")

print('=== LOGS DO SERVICO (ULTIMAS 20 LINHAS) ===')
print(run("journalctl -u hemn_cloud.service --no-pager -n 20"))

client.close()
