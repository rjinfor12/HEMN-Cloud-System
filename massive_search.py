import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_massive_search():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        script_content = """
import subprocess
import json

def run_q(q):
    cmd = ['clickhouse-client', '--query', q]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip().split('\\n')

queries = {
    "socios_full_name": "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE 'ROGERIO ELIAS DO NASCIMENTO JUNIOR%'",
    "socios_unmasked_cpf": "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = '09752279473'",
    "empresas_full_name": "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE 'ROGERIO ELIAS DO NASCIMENTO JUNIOR%'",
    "estab_email_pattern": "SELECT cnpj_basico, email FROM hemn.estabelecimento WHERE upper(email) LIKE '%ROGERIO%ELIAS%' LIMIT 10",
    "socios_partial_name": "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE 'ROGERIO ELIAS%' AND cnpj_cpf_socio LIKE '***522794**'",
    "all_meis_rogerio": "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE '%ROGERIO%' AND upper(razao_social) LIKE '%ELIAS%' AND upper(razao_social) LIKE '%NASCIMENTO%'"
}

results = {}
for k, q in queries.items():
    results[k] = run_q(q)

with open('/tmp/massive_rogerio.json', 'w') as f:
    json.dump(results, f, indent=2)
"""
        # Upload script
        sftp = client.open_sftp()
        with sftp.open('/tmp/remote_massive.py', 'w') as f:
            f.write(script_content)
        
        # Run script
        client.exec_command('python3 /tmp/remote_massive.py')
        
        # Download result
        sftp.get('/tmp/massive_rogerio.json', 'massive_rogerio.json')
        sftp.close()
        print("Downloaded results to massive_rogerio.json")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_massive_search()
