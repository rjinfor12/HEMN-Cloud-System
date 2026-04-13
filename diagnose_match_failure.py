import paramiko

def diagnose_zero_results():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        # Test 1: Count establishments in Recife with situacao_cadastral = '02' (Ativas)
        # Using 02 because it's the standard, but let's check what's actually there
        cmd1 = "clickhouse-client --query \"SELECT situacao_cadastral, count(1) FROM hemn.estabelecimento WHERE uf='PE' AND municipio='2531' GROUP BY situacao_cadastral\""
        print(f"\n--- {cmd1} ---")
        stdin, stdout, stderr = c.exec_command(cmd1)
        print(stdout.read().decode())
        
        # Test 2: Sample real CNPJs from Recife to see format
        cmd2 = "clickhouse-client --query \"SELECT cnpj, length(cnpj) FROM hemn.estabelecimento WHERE uf='PE' AND municipio='2531' LIMIT 5\""
        print(f"\n--- {cmd2} ---")
        stdin, stdout, stderr = c.exec_command(cmd2)
        print(stdout.read().decode())
        
        # Test 3: Check if SUBSTRING(cnpj, 1, 8) matches anything in empresas
        cmd3 = "clickhouse-client --query \"SELECT e.cnpj_basico, count(1) FROM hemn.empresas e INNER JOIN (SELECT SUBSTRING(cnpj, 1, 8) as b FROM hemn.estabelecimento WHERE uf='PE' AND municipio='2531' LIMIT 10) AS s ON e.cnpj_basico = s.b GROUP BY e.cnpj_basico\""
        print(f"\n--- {cmd3} ---")
        stdin, stdout, stderr = c.exec_command(cmd3)
        print(stdout.read().decode())
        
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_zero_results()
