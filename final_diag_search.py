import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_final_search():
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

# 1. Exact Name Search in SOCIOS
res1 = run_q("SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE 'ROGERIO ELIAS DO NASCIMENTO%'")

# 2. Search by CPF mask
res2 = run_q("SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = '***522794**'")

# 3. Search MEIs
res3 = run_q("SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE 'ROGERIO ELIAS DO NASCIMENTO%'")

results = {
    "socios_by_name": res1,
    "socios_by_cpf": res2,
    "mei_by_name": res3
}

with open('/tmp/final_rogerio.json', 'w') as f:
    json.dump(results, f, indent=2)
"""
        # Upload script
        sftp = client.open_sftp()
        with sftp.open('/tmp/remote_final.py', 'w') as f:
            f.write(script_content)
        
        # Run script
        client.exec_command('python3 /tmp/remote_final.py')
        
        # Download result
        sftp.get('/tmp/final_rogerio.json', 'final_rogerio.json')
        sftp.close()
        print("Downloaded results to final_rogerio.json")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_final_search()
