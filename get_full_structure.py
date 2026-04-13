import paramiko

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def get_structure():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Check establishment structure
        stdin, stdout, stderr = client.exec_command("clickhouse-client --query 'SHOW CREATE TABLE hemn.estabelecimento'")
        print("--- ESTABELECIMENTO ---")
        print(stdout.read().decode())
        
        # Check empresas structure
        stdin, stdout, stderr = client.exec_command("clickhouse-client --query 'SHOW CREATE TABLE hemn.empresas'")
        print("--- EMPRESAS ---")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_structure()
