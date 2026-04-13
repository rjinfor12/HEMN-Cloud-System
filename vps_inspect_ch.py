import paramiko

def inspect_vps():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        print("--- ClickHouse Databases ---")
        stdin, stdout, stderr = c.exec_command('clickhouse-client -q "SHOW DATABASES"')
        print(stdout.read().decode())
        
        print("--- hemn or cnpj status ---")
        stdin, stdout, stderr = c.exec_command('clickhouse-client -q "SELECT name FROM system.databases WHERE name IN (\'hemn\', \'cnpj\')"')
        print(stdout.read().decode())

        print("--- Tables in hemn (if exists) ---")
        stdin, stdout, stderr = c.exec_command('clickhouse-client -q "SHOW TABLES FROM hemn"')
        print(stdout.read().decode())

        print("--- Tables in cnpj (if exists) ---")
        stdin, stdout, stderr = c.exec_command('clickhouse-client -q "SHOW TABLES FROM cnpj"')
        print(stdout.read().decode())

        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_vps()
