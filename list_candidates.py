import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def list_candidates():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        name = "ROGERIO ELIAS"
        print(f"Listing all empresas matching: {name}%")
        
        q = f"SELECT DISTINCT razao_social FROM hemn.empresas WHERE razao_social LIKE '{name}%' LIMIT 50"
        cmd = f"clickhouse-client --query \"{q}\""
        stdin, stdout, stderr = client.exec_command(cmd)
        
        result = stdout.read().decode()
        print(result)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    list_candidates()
