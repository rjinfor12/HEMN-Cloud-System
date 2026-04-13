import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: print("OUT:", out.strip())
    if err: print("ERR:", err.strip())

print("--- Step 1: Syncing SQLite Databases (Logins/Tasks) ---")
# Copia os bancos de dados de produção para dev
run_cmd(client, "cp /var/www/hemn_cloud/*.db /var/www/hemn_cloud_dev/")
run_cmd(client, "chown root:root /var/www/hemn_cloud_dev/*.db")
run_cmd(client, "chmod 666 /var/www/hemn_cloud_dev/*.db")

print("--- Step 2: Syncing ClickHouse Tables (Data) ---")
# Para tabelas de dados, precisamos inserir os registros (apenas o que estiver no hemn)
# Notar: Inserir bilhões de linhas pode demorar. 
# Vamos focar nas tabelas de configurações e leads primeiro.
tables_to_sync = ["_metadata", "lookup_matrix", "cnae", "municipio", "natureza_juridica", "qualificacao_socio", "simples"]
for t in tables_to_sync:
    run_cmd(client, f'clickhouse-client --query "INSERT INTO hemn_dev.{t} SELECT * FROM hemn.{t}"')

print("--- Final Step: Restart Dev Service ---")
run_cmd(client, "systemctl restart hemn_cloud_dev.service")

client.close()
print("Mirroring script finished.")
