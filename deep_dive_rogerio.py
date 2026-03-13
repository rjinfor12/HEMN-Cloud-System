import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def deep_dive():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # User's target
        # Name: ROGERIO ELIAS DO NASCIMENTO JUNIOR
        # CPF: 09752279473 -> middle 522794
        
        print("--- Search 1: Socios with name containing 'ROGERIO' and middle digits '522794' ---")
        q1 = "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE nome_socio LIKE '%ROGERIO%' AND cnpj_cpf_socio LIKE '%522794%'"
        cmd1 = f"clickhouse-client --query \"{q1}\""
        stdin, stdout, stderr = client.exec_command(cmd1)
        print(stdout.read().decode())

        print("--- Search 2: Socios with JUST '522794' (listing names to verify) ---")
        q2 = "SELECT DISTINCT nome_socio, cnpj_cpf_socio FROM hemn.socios WHERE cnpj_cpf_socio LIKE '%522794%' LIMIT 20"
        cmd2 = f"clickhouse-client --query \"{q2}\""
        stdin, stdout, stderr = client.exec_command(cmd2)
        print(stdout.read().decode())

        print("--- Search 3: Empresas with name containing 'ROGERIO' and 'NASCIMENTO' ---")
        q3 = "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '%ROGERIO%NASCIMENTO%' LIMIT 10"
        cmd3 = f"clickhouse-client --query \"{q3}\""
        stdin, stdout, stderr = client.exec_command(cmd3)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deep_dive()
