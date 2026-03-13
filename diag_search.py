import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_diagnostics():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        import sys
        # Ensure we can print unicode on Windows
        if sys.platform == 'win32':
             import io
             sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

        # 1. Extract frontend keys from index.html
        print("--- EXTRACTING FRONTEND KEYS ---")
        cmd_keys = "grep -A 100 'runManualSearch' /var/www/hemn_cloud/static/index.html"
        stdin, stdout, stderr = client.exec_command(cmd_keys)
        print(stdout.read().decode('utf-8', errors='replace'))

        # 2. Search for all companies of Rogerio by name variations in SOCIOS
        print("\n--- SEARCHING SOCIOS BY NAME VARIATIONS ---")
        names = ["ROGERIO ELIAS DO NASCIMENTO JUNIOR", "ROGERIO ELIAS DO NASCIMENTO", "ROGERIO ELIAS"]
        for name in names:
            q = f"SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE nome_socio LIKE '{name}%' LIMIT 10"
            cmd = f"clickhouse-client --query \"{q}\""
            stdin, stdout, stderr = client.exec_command(cmd)
            res = stdout.read().decode('utf-8', errors='replace')
            if res:
                print(f"Results for '{name}':")
                print(res)

        # 3. Search for EMPRESAS that might be MEIs or have him as owner but didn't show up
        print("\n--- SEARCHING EMPRESAS BY NAME/CPF ---")
        q_emp = "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '%ROGERIO%ELIAS%NASCIMENTO%' OR razao_social LIKE '%09752279473%'"
        cmd_emp = f"clickhouse-client --query \"{q_emp}\""
        stdin, stdout, stderr = client.exec_command(cmd_emp)
        print(stdout.read().decode('utf-8', errors='replace'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_diagnostics()
