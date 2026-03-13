"""
Deploy rapido: apenas envia o HEMN_Cloud_Server.py corrigido e reinicia o servico.
"""
import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

LOCAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HEMN_Cloud_Server.py")
REMOTE_PATH = "/var/www/hemn_cloud/HEMN_Cloud_Server.py"

def run_cmd(client, cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    if out: print("OUT:", out)
    if err: print("ERR:", err)
    return exit_status

print(f"Conectando ao VPS {host}:{port}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print(f"Fazendo upload de {LOCAL_FILE} -> {REMOTE_PATH}")
sftp = client.open_sftp()
sftp.put(LOCAL_FILE, REMOTE_PATH)
sftp.close()
print("Upload concluido!")

print("Reiniciando servico hemn_cloud...")
run_cmd(client, "systemctl restart hemn_cloud.service")

print("Verificando status do servico...")
run_cmd(client, "systemctl status hemn_cloud.service --no-pager -l")

print("Verificando se o endpoint /webhook/asaas existe...")
run_cmd(client, "curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/webhook/asaas -H 'Content-Type: application/json' -d '{\"event\":\"PING\",\"payment\":{}}'")

client.close()
print("\nDeploy concluido! Webhook corrigido e servico reiniciado.")
print("Verifique os logs em: /var/www/hemn_cloud/webhook_asaas.log")
