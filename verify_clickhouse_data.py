import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def verify_counts():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        tables = ["empresas", "estabelecimento", "socios", "municipio"]
        results = {}
        
        print(f"{'Table':<20} | {'Count':<15}")
        print("-" * 38)
        
        for table in tables:
            # Using a simpler command to avoid quoting issues
            cmd = f"clickhouse-client --query \"SELECT count() FROM hemn.{table}\""
            stdin, stdout, stderr = client.exec_command(cmd)
            count = stdout.read().decode().strip()
            print(f"{table:<20} | {count:<15}")
            
        print("\nSample Search ('PETROBRAS'):")
        cmd = "clickhouse-client --query \"SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE 'PETROBRAS%' LIMIT 5\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode().strip())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_counts()
