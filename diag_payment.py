"""
Diagnostica o pagamento de teste feito pelo usuario.
Verifica: webhook log, banco de dados asaas_payments, payments no ASAAS API.
"""
import paramiko, os, requests, json

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

ASAAS_API_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjEzMDJlNTFjLTgwODgtNGRmNi1iZTA3LWVkYmE0YzI5Y2UwYzo6JGFhY2hfODExNDEyNmEtZWI2Yy00OGFlLWI4OTktZjYyZjljMDdkNmIw"
ASAAS_URL = "https://www.asaas.com/api/v3"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("=" * 60)
print("1. WEBHOOK LOG (ultimas 50 linhas)")
print("=" * 60)
print(run("tail -50 /var/www/hemn_cloud/webhook_asaas.log 2>/dev/null || echo 'Log vazio'"))

print("=" * 60)
print("2. PAGAMENTOS NO BANCO LOCAL (asaas_payments)")
print("=" * 60)
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT id, username, amount, credits, status, created_at, confirmed_at FROM asaas_payments ORDER BY rowid DESC LIMIT 10;'"))

print("=" * 60)
print("3. TRANSACOES RECENTES (credit_transactions)")
print("=" * 60)
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT username, type, amount, module, description, timestamp FROM credit_transactions ORDER BY rowid DESC LIMIT 10;'"))

print("=" * 60)
print("4. ULTIMAS LINHAS DO LOG DO SERVICO")
print("=" * 60)
print(run("journalctl -u hemn_cloud.service --no-pager -n 30 2>/dev/null || tail -30 /var/www/hemn_cloud/server_error.log 2>/dev/null || echo 'Sem logs'"))

client.close()

print("=" * 60)
print("5. PAGAMENTOS RECENTES NO ASAAS API")
print("=" * 60)
headers = {"access_token": ASAAS_API_KEY, "Content-Type": "application/json"}
r = requests.get(f"{ASAAS_URL}/payments?limit=5", headers=headers)
data = r.json()
for p in data.get("data", []):
    print(f"  ID: {p.get('id')}")
    print(f"  Status: {p.get('status')}")
    print(f"  Valor: R$ {p.get('value')}")
    print(f"  Tipo: {p.get('billingType')}")
    print(f"  Data: {p.get('dateCreated')}")
    print(f"  ExternalRef: {p.get('externalReference')}")
    print()
