import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: print("OUT:", out.strip())
    if err: print("ERR:", err.strip())

print("--- Verificando Leads PE (Clínicas) ---")
# Usaremos uma query que conta para não sobrecarregar
run_cmd(client, 'clickhouse-client --query "SELECT count() FROM hemn.leads WHERE uf = \'PE\'"')
run_cmd(client, 'clickhouse-client --query "SELECT count() FROM hemn.leads_v2 WHERE uf = \'PE\'"')

print("--- Sincronizando Leads PE para Dev ---")
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.leads SELECT * FROM hemn.leads WHERE uf = \'PE\'"')
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.leads_v2 SELECT * FROM hemn.leads_v2 WHERE uf = \'PE\'"')

print("--- Verificação em Dev ---")
run_cmd(client, 'clickhouse-client --query "SELECT uf, count() FROM hemn_dev.leads GROUP BY uf"')

client.close()
print("Sincronização de Leads PF (Clínicas) para PE finalizada.")
