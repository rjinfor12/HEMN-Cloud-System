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

print("--- Sincronizando Estabelecimentos PE ---")
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.estabelecimento SELECT * FROM hemn.estabelecimento WHERE uf = \'PE\'"')

print("--- Sincronizando Empresas (Base do CNPJ) ---")
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.empresas SELECT * FROM hemn.empresas WHERE cnpj_base IN (SELECT cnpj_base FROM hemn_dev.estabelecimento)"')

print("--- Sincronizando Sócios ---")
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.socios SELECT * FROM hemn.socios WHERE cnpj_base IN (SELECT cnpj_base FROM hemn_dev.estabelecimento)"')

print("--- Sincronizando Simples Nacional ---")
run_cmd(client, 'clickhouse-client --query "INSERT INTO hemn_dev.simples SELECT * FROM hemn.simples WHERE cnpj_base IN (SELECT cnpj_base FROM hemn_dev.estabelecimento)"')

print("--- Sincronizando Outras Tabelas de Apoio ---")
# Já fizemos no sync anterior, mas garantindo CNAEs e Municípios
tables = ["cnae", "municipio"]
for t in tables:
    run_cmd(client, f'clickhouse-client --query "INSERT INTO hemn_dev.{t} SELECT * FROM hemn.{t} WHERE 1"')

print("--- Verificação Final em Dev ---")
run_cmd(client, 'clickhouse-client --query "SELECT uf, count() FROM hemn_dev.estabelecimento GROUP BY uf"')

client.close()
print("Sincronização de dados de PE finalizada.")
