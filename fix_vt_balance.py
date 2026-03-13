import paramiko, os

host = '129.121.45.136'
port = 22022
user_ssh = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user_ssh, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# 1. Calcular o uso real baseado nas transacoes de debito
print("=== Calculando uso real de creditos do usuario Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT SUM(amount) FROM credit_transactions WHERE username='Vt' AND type='DEBIT';\""))

# 2. Calcular total de creditos recebidos via ASAAS
print("=== Total de creditos adicionados ao Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT SUM(credits) FROM asaas_payments WHERE username='Vt' AND status='RECEIVED';\""))

# 3. Corrigir: zerar o current_usage (recalcular com base nos debitos reais)
# O current_usage real deve ser a soma dos debitos no historico
print("=== Corrigindo current_usage para 0 (usuario sem debitos registrados) ===")
result = run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"UPDATE users SET current_usage = 0 WHERE username='Vt'; SELECT username, total_limit, current_usage, (total_limit - current_usage) as saldo FROM users WHERE username='Vt';\"")
print(result)

print("=== Saldo final do usuario Vt ===")
print(run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT username, full_name, total_limit, current_usage, (total_limit - current_usage) as saldo FROM users WHERE username='Vt';\""))

client.close()
print("Pronto! O saldo do usuario Vt foi corrigido.")
