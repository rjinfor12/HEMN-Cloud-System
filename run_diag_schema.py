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

diag_script = r"""
import pandas as pd
import clickhouse_connect

try:
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # 1. Check schemas
    print("--- 1. SCHEMAS ---")
    print("Establishment Schema:")
    print(client.query("DESCRIBE hemn.estabelecimento").result_rows)
    print("\nEmpresas Schema:")
    print(client.query("DESCRIBE hemn.empresas").result_rows)

    # 2. Ground Truth Counts (CE, ATIVA, MEI)
    print("\n--- 2. COUNTS (Limited to avoid timeout) ---")
    # count total establishments in CE active
    q_ce = "SELECT count() FROM hemn.estabelecimento WHERE uf = 'CE' AND situacao_cadastral = '02'"
    print(f"CE ATIVA Establishments: {client.query(q_ce).result_rows[0][0]:,}")
    
    # count establishments in CE active that are MEI (using a more efficient join if possible)
    # Using ANY JOIN to be safe on memory
    q_mei = '''
        SELECT count() 
        FROM hemn.estabelecimento estab
        INNER JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
        WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135'
    '''
    # I'll try it with a smaller subset first if it fails, but let's try ANY
    q_mei_any = '''
        SELECT count() 
        FROM hemn.estabelecimento estab
        ANY INNER JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
        WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135'
    '''
    # Wait, ANY JOIN on companies might be better because there is only one company per base CNPJ.
    print(f"MEI CE ATIVA (ANY JOIN): {client.query(q_mei_any).result_rows[0][0]:,}")

    # 3. Sample Data check
    q_sample = '''
        SELECT e.razao_social, estab.logradouro, estab.numero, estab.bairro, estab.cep
        FROM hemn.estabelecimento estab
        ANY INNER JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
        WHERE estab.uf = 'CE' AND estab.situacao_cadastral = '02' AND e.natureza_juridica = '2135'
        LIMIT 5
    '''
    res = client.query(q_sample)
    print("\n--- 3. SAMPLE DATA ---")
    for row in res.result_rows:
        print(row)

except Exception as e:
    print(f"Erro: {e}")
"""

print('=== EXECUTANDO DIAGNÓSTICO DE SCHEMA E CONTAGEM NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/diag_schema_count.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/diag_schema_count.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
