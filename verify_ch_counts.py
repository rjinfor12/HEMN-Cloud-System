import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run_ch(query):
    cmd = f'clickhouse-client -q "{query}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode().strip()

print("--- CLIQUEHOUSE TABLE AUDIT ---")
tables = ["empresas", "estabelecimento", "socios", "simples", "municipio", "paises", "natureza_juridica", "qualificacao_socio", "cnae", "motivo"]

print(f"{'Table':<20} | {'Production (hemn)':<20} | {'Update (tmp)':<20}")
print("-" * 65)

for t in tables:
    try:
        count_prod = run_ch(f"SELECT count() FROM hemn.{t}")
    except:
        count_prod = "ERROR/MISSING"
        
    try:
        count_tmp = run_ch(f"SELECT count() FROM hemn_update_tmp.{t}")
    except:
        count_tmp = "ERROR/MISSING"
        
    print(f"{t:<20} | {count_prod:<20} | {count_tmp:<20}")

client.close()
