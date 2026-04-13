import paramiko

def check_join_types():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        # Test 1: Describe both tables
        cmd1 = "clickhouse-client --query 'DESCRIBE hemn.estabelecimento'"
        cmd2 = "clickhouse-client --query 'DESCRIBE hemn.empresas'"
        
        # Test 2: Check counts
        cmd3 = "clickhouse-client --query 'SELECT count(1) FROM hemn.estabelecimento WHERE uf=\"PE\" AND municipio=\"2531\"'"
        cmd4 = "clickhouse-client --query 'SELECT count(1) FROM hemn.empresas'"
        
        for cmd in [cmd1, cmd2, cmd3, cmd4]:
            print(f"\n--- {cmd} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            print(stdout.read().decode())
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_join_types()
