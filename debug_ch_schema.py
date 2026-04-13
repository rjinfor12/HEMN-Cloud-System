import paramiko

def check_db():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        commands = [
            "clickhouse-client --query 'DESCRIBE hemn.estabelecimento'",
            "clickhouse-client --query 'SELECT * FROM hemn.municipio WHERE descricao LIKE \"%RECIFE%\"'"
        ]
        
        for cmd in commands:
            print(f"\n--- {cmd} ---")
            stdin, stdout, stderr = c.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
        c.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
