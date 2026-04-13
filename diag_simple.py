import paramiko

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def run_diag():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Check table structures
        stdin, stdout, stderr = client.exec_command("clickhouse-client --query 'SHOW CREATE TABLE hemn.estabelecimento'")
        print(f"ESTADO: {stdout.read().decode()}")
        
        stdin, stdout, stderr = client.exec_command("clickhouse-client --query 'SHOW CREATE TABLE hemn.empresas'")
        print(f"EMPRESAS: {stdout.read().decode()}")
        
        # Check system memory
        stdin, stdout, stderr = client.exec_command("free -h")
        print(f"MEM: {stdout.read().decode()}")
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_diag()
