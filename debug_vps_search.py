import paramiko
import os
import json

def debug_vps_search():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        # Exact params from the screenshot
        name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
        cpf = "09752279473"

        # Create a temp python script on the VPS to run the actual CloudEngineVps logic
        debug_script = f"""
import sys
import pandas as pd
from cloud_engine_vps import CloudEngineVps

def run_debug():
    engine = CloudEngineVps()
    name = "{name}"
    cpf = "{cpf}"
    print(f"DEBUG: Searching for Name='{{name}}', CPF='{{cpf}}'")
    results = engine.deep_search(name, cpf)
    print("--- RESULTS ---")
    if not results.empty:
        print(results[['razao_social', 'cnpj_completo', 'nome_socio', 'cnpj_cpf_socio']].to_string())
    else:
        print("No results found.")

if __name__ == '__main__':
    run_debug()
"""
        # Upload debug script
        sftp = client.open_sftp()
        with sftp.file('/var/www/hemn_cloud/debug_search_leak.py', 'w') as f:
            f.write(debug_script)
        sftp.close()

        # Run debug script using the venv
        print("--- Executing Debug Script on VPS ---")
        stdin, stdout, stderr = client.exec_command("cd /var/www/hemn_cloud && ./venv/bin/python debug_search_leak.py")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_vps_search()
