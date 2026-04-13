import paramiko

def final_diagnose():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        # Test 1: Search for a specific basic CNPJ from Recife in the empresas table
        # We know 06862422 is a valid basic CNPJ from my previous diagnostic
        cmd1 = "clickhouse-client --query \"SELECT cnpj_basico, razao_social FROM hemn.empresas WHERE cnpj_basico = '06862422'\""
        print(f"\n--- {cmd1} ---")
        stdin, stdout, stderr = c.exec_command(cmd1)
        print(stdout.read().decode())
        
        # Test 2: Check for any matching basic CNPJ in PE
        cmd2 = "clickhouse-client --query \"SELECT count(1) FROM hemn.empresas e INNER JOIN hemn.estabelecimento estab ON e.cnpj_basico = SUBSTRING(estab.cnpj, 1, 8) WHERE estab.uf = 'PE' AND estab.municipio = '2531' AND estab.situacao_cadastral = '02'\""
        print(f"\n--- {cmd2} ---")
        stdin, stdout, stderr = c.exec_command(cmd2)
        print(stdout.read().decode())
        
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    final_diagnose()
