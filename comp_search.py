import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_comprehensive_search():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # 1. Get ALL partners for his CPF mask
        print("--- ALL PARTNERS WITH MASK ***522794** ---")
        q1 = "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = '***522794**'"
        cmd1 = f"clickhouse-client --query \"{q1}\""
        stdin, stdout, stderr = client.exec_command(cmd1)
        print(stdout.read().decode())

        # 2. Get ALL records for his full name (variations)
        print("\n--- ALL RECORDS FOR NAME VARIATIONS ---")
        names_to_check = ["ROGERIO ELIAS DO NASCIMENTO JUNIOR", "ROGERIO ELIAS DO NASCIMENTO"]
        for name in names_to_check:
            print(f"Checking: {name}")
            q2 = f"SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE upper(nome_socio) = '{name.upper()}'"
            cmd2 = f"clickhouse-client --query \"{q2}\""
            stdin, stdout, stderr = client.exec_command(cmd2)
            print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_comprehensive_search()
