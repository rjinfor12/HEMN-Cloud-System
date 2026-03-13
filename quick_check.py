import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_quick_query():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # Identify the companies
        cnpjs = ["23573445", "15087318"]
        for cnpj in cnpjs:
            print(f"--- CNPJ BASICO: {cnpj} ---")
            q = f"SELECT razao_social FROM hemn.empresas WHERE cnpj_basico = '{cnpj}'"
            cmd = f"clickhouse-client --query \\\"{q}\\\""
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_quick_query()
