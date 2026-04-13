import paramiko

def check_pe_data():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        # Test 1: See real municipio codes in PE
        cmd1 = "clickhouse-client --query \"SELECT municipio, count(1) FROM hemn.estabelecimento WHERE uf = 'PE' GROUP BY municipio ORDER BY count(1) DESC LIMIT 10\""
        print(f"\n--- {cmd1} ---")
        stdin, stdout, stderr = c.exec_command(cmd1)
        print(stdout.read().decode())
        
        # Test 2: Search for Recife in municipio table specifically
        cmd2 = "clickhouse-client --query \"SELECT codigo, descricao FROM hemn.municipio WHERE descricao LIKE '%RECIFE%'\""
        print(f"\n--- {cmd2} ---")
        stdin, stdout, stderr = c.exec_command(cmd2)
        print(stdout.read().decode())
        
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pe_data()
