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

# 1. Create temporary table
print("Creating temporary table leads_v2...")
client.exec_command("clickhouse-client --query \"CREATE TABLE hemn.leads_v2 AS hemn.leads\"")

# 2. Insert padded data
print("Migrating data with padding (this may take a few minutes)...")
query_mig = "INSERT INTO hemn.leads_v2 SELECT lpad(cpf, 11, '0'), nome, dt_nascimento, tel_fixo1, celular1, uf, regiao FROM hemn.leads"
run(f"clickhouse-client --query \"{query_mig}\"")

# 3. Swap tables
print("Swapping tables...")
run("clickhouse-client --query \"EXCHANGE TABLES hemn.leads AND hemn.leads_v2\"")

# 4. Optional: Drop old table (v2 now contains the original data)
# run("clickhouse-client --query \"DROP TABLE hemn.leads_v2\"")

print("Migration complete!")
client.close()
