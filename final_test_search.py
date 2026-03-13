import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def final_test():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # Scenario: User searches for ROGERIO who is NOT in the database, 
        # but shares a CPF mask with NAETE.
        name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
        mask = "***522794**"
        
        print(f"Searching for: {name} AND {mask}")
        
        q = f"SELECT s.nome_socio, s.cnpj_cpf_socio FROM hemn.socios s WHERE s.nome_socio LIKE '{name}%' AND s.cnpj_cpf_socio = '{mask}'"
        
        cmd = f"clickhouse-client --query \"{q}\""
        stdin, stdout, stderr = client.exec_command(cmd)
        
        result = stdout.read().decode()
        if not result.strip():
            print("CORRECT: No results found for this mismatching combination.")
        else:
            print("ERROR: Found results that should have been filtered out:")
            print(result)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    final_test()
