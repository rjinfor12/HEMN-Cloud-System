import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def test_search():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # Test case for the user: ROGERIO ELIAS DO NASCIMENTO JUNIOR
        # CPF 09752279473 -> mask ***522794**
        name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
        mask = "***522794**"
        
        print(f"Testing search for: {name} AND {mask}")
        
        q = f"SELECT b.razao_social, s.nome_socio, s.cnpj_cpf_socio FROM hemn.socios s JOIN hemn.empresas b ON s.cnpj_basico = b.cnpj_basico WHERE s.nome_socio = '{name}' AND s.cnpj_cpf_socio = '{mask}'"
        
        cmd = f"clickhouse-client --query \"{q}\""
        stdin, stdout, stderr = client.exec_command(cmd)
        
        result = stdout.read().decode()
        if result:
            print("--- Results Found ---")
            print(result)
        else:
            print("--- No Results Found (trying LIKE) ---")
            q_like = f"SELECT b.razao_social, s.nome_socio, s.cnpj_cpf_socio FROM hemn.socios s JOIN hemn.empresas b ON s.cnpj_basico = b.cnpj_basico WHERE s.nome_socio LIKE 'ROGERIO ELIAS%' AND s.cnpj_cpf_socio = '{mask}'"
            cmd_like = f"clickhouse-client --query \"{q_like}\""
            stdin, stdout, stderr = client.exec_command(cmd_like)
            print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test_search()
