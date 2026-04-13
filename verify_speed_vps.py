import paramiko
import time

def verify_speed():
    host = '86.48.17.194'
    user = 'root'
    pw = '^QP67kXax9AyuvF%'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, username=user, password=pw)
        
        # Test query for AC (Acre) - smaller subset to check speed
        query = "SELECT count() FROM hemn.estabelecimento estab INNER JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico WHERE estab.uf = 'AC' AND estab.situacao_cadastral = '02'"
        
        print(f"Running test query: {query}")
        start = time.time()
        stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
        result = stdout.read().decode().strip()
        duration = time.time() - start
        
        print(f"Result: {result} records found.")
        print(f"Duration: {duration:.2f} seconds.")
        
        if duration < 10:
            print("VERIFICATION SUCCESSFUL: Performance is back to normal.")
        else:
            print("VERIFICATION WARNING: Still slower than expected (>10s for AC).")
            
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_speed()
