import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def bread_search():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        name = "ROGERIO ELIAS"
        print(f"--- Searching for ANY socio starting with '{name}' ---")
        q1 = f"SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE nome_socio LIKE '{name}%' LIMIT 100"
        cmd1 = f"clickhouse-client --query \"{q1}\""
        stdin, stdout, stderr = client.exec_command(cmd1)
        print(stdout.read().decode())

        print(f"--- Searching for ANY empresa starting with '{name}' ---")
        q2 = f"SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '{name}%' LIMIT 100"
        cmd2 = f"clickhouse-client --query \"{q2}\""
        stdin, stdout, stderr = client.exec_command(cmd2)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    bread_search()
