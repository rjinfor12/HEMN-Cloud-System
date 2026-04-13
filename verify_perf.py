import paramiko
import time

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def verify():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Test Query with and without projection optimization
        query = "SELECT count() FROM hemn.estabelecimento AS estab INNER JOIN hemn.empresas AS e ON e.cnpj_basico = estab.cnpj_basico PREWHERE uf = 'AC' AND situacao_cadastral = '02' SETTINGS optimize_projection = 1"
        
        print(f"Executing: {query}")
        start = time.time()
        stdin, stdout, stderr = client.exec_command(f"clickhouse-client --query \"{query}\"")
        result = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        end = time.time()
        
        print(f"Result: {result}")
        print(f"Time: {end - start:.3f}s")
        if err: print(f"ERR: {err}")
        
        # Check if projection was used
        stdin, stdout, stderr = client.exec_command("clickhouse-client --query \"SELECT query, query_duration_ms, read_rows, memory_usage FROM system.query_log WHERE type = 'QueryFinish' AND query LIKE '%PREWHERE uf = %' ORDER BY event_time DESC LIMIT 1\"")
        print("\n--- Last Query Stats ---")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify()
