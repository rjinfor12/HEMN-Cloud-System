import paramiko

def audit_ch():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        print("--- AUDITORIA CLICKHOUSE ---")
        
        # 1. Total Rows per Database
        print("\n[DB SIZES]")
        cmd = 'clickhouse-client -q "SELECT database, count() FROM system.tables GROUP BY database"'
        stdin, stdout, stderr = c.exec_command(cmd)
        print(stdout.read().decode())
        
        # 2. Schema of hemn.estabelecimento
        print("\n[SCHEMA hemn.estabelecimento]")
        cmd = 'clickhouse-client -q "DESCRIBE hemn.estabelecimento"'
        stdin, stdout, stderr = c.exec_command(cmd)
        print(stdout.read().decode())
        
        # 3. Check for RECIFE leads in hemn
        print("\n[RECIFE CHECK in hemn.estabelecimento]")
        # Try both direct name check (if COLUMN exists) or join
        cmd = 'clickhouse-client -q "SELECT count() FROM hemn.estabelecimento WHERE uf=\'PE\'"'
        stdin, stdout, stderr = c.exec_command(cmd)
        print(f"Total PE Leads in hemn.estabelecimento: {stdout.read().decode().strip()}")

        c.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    audit_ch()
