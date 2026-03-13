import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def check_schema():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        # Check socios schema
        cmd = "clickhouse-client --query 'DESCRIBE hemn.socios'"
        print(f"Schema for hemn.socios:")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # Check empresas schema
        cmd = "clickhouse-client --query 'DESCRIBE hemn.empresas'"
        print(f"\nSchema for hemn.empresas:")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_schema()
