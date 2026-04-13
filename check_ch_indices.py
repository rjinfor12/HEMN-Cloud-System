import paramiko

def check_indices_ssh():
    host = '86.48.17.194'
    user = 'root'
    pw = '^QP67kXax9AyuvF%'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, password=pw)
        
        # Tentando pegar apenas as colunas de ordenação
        cmd = 'clickhouse-client --query "SELECT name, sorting_key FROM system.tables WHERE database = \'hemn\' AND name IN (\'estabelecimento\', \'empresas\')"'
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"OUT: {stdout.read().decode()}")
        print(f"ERR: {stderr.read().decode()}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_indices_ssh()
