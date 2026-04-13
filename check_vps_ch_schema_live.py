import paramiko
import os

def check_schema():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        commands = [
            ("SCHEMA ESTABELECIMENTO", 'clickhouse-client -q "SHOW CREATE TABLE hemn.estabelecimento"'),
            ("SCHEMA EMPRESAS", 'clickhouse-client -q "SHOW CREATE TABLE hemn.empresas"'),
            ("ROW COUNTS", 'clickhouse-client -q "SELECT table, count(*) FROM system.parts WHERE database=\'hemn\' AND active GROUP BY table"'),
            ("DISK USAGE", 'clickhouse-client -q "SELECT table, formatReadableSize(sum(data_compressed_bytes)) FROM system.parts WHERE database=\'hemn\' AND active GROUP BY table"')
        ]
        
        for title, cmd in commands:
            print(f"\n--- {title} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            if out: print(out)
            if err: print(f"Error: {err}")
            
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
