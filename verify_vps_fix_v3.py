import paramiko
import os

def verify_vps_fix():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        verify_script = """
import sys
import pandas as pd
from cloud_engine import CloudEngine

def run_verify():
    engine = CloudEngine()
    name = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'
    cpf = '09752279473'
    print(f'DEBUG: Searching for Name="{name}", CPF="{cpf}"')
    results = engine.deep_search(name, cpf)
    print('--- RESULTS ---')
    if not results.empty:
        # Show CNAE and MEI columns
        # Note: In the query, cnae is mapped to 'nome_socio' and MEI to 'cnpj_cpf_socio'
        print(results[['razao_social', 'nome_socio', 'cnpj_cpf_socio']].to_string())
        print(f'Total results: {len(results)}')
    else:
        print('No results found.')

if __name__ == "__main__":
    run_verify()
"""
        sftp = client.open_sftp()
        with sftp.file('/var/www/hemn_cloud/verify_fix_v3.py', 'w') as f:
            f.write(verify_script)
        sftp.close()

        print("--- Executing Verification on VPS ---")
        stdin, stdout, stderr = client.exec_command("cd /var/www/hemn_cloud && ./venv/bin/python verify_fix_v3.py")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_vps_fix()
