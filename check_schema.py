import paramiko
import os

def get_db_schema():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- NATUREZA JURIDICA / PORTE EMPRESA (MEI CHECK) ---")
        query = "SELECT natureza_juridica, porte_empresa, count() FROM hemn.empresas GROUP BY natureza_juridica, porte_empresa LIMIT 20"
        stdin, stdout, stderr = client.exec_command(f"clickhouse-client --query '{query}'")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_db_schema()
