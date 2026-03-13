import paramiko
import os
import time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def execute_remote(client, command):
    print(f"Executing: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"STDOUT: {out.encode('ascii', 'replace').decode()}")
    if err: print(f"STDERR: {err.encode('ascii', 'replace').decode()}")
    return out, err

def finalize_migration():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        print("Checking dependencies on server...")
        execute_remote(client, "apt-get update && apt-get install -y python3-pip")
        execute_remote(client, "pip3 install clickhouse-connect")
        
        # We need to make sure clickhouse is running
        execute_remote(client, "systemctl status clickhouse-server || systemctl start clickhouse-server")
        
        # Upload migration and setup scripts
        sftp = client.open_sftp()
        sftp.put('setup_clickhouse.py', '/tmp/setup_clickhouse.py')
        sftp.put('migrate_to_clickhouse.py', '/tmp/migrate_to_clickhouse.py')
        sftp.close()
        
        print("Setting up ClickHouse schema...")
        execute_remote(client, "python3 /tmp/setup_clickhouse.py")
        
        print("Starting data migration from SQLite to ClickHouse...")
        execute_remote(client, "python3 /tmp/migrate_to_clickhouse.py")
        
        print("Verifying record counts in ClickHouse...")
        for table in ["empresas", "estabelecimento", "socios", "municipio"]:
            out, err = execute_remote(client, f'clickhouse-client --query "SELECT count() FROM hemn.{table}"')
            print(f"Table {table}: {out} records")
        
        print("Migration process finished!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    finalize_migration()
