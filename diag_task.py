import paramiko

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def diag():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Check Task ID 0094a211 from screenshot
        tid = "0094a211"
        
        # 1. Check Task Stats in SQLite
        print(f"--- SQLite Status for {tid} ---")
        cmd_sqlite = f"sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT status, progress, message FROM background_tasks WHERE id LIKE '{tid}%'\""
        stdin, stdout, stderr = client.exec_command(cmd_sqlite)
        print(stdout.read().decode())

        # 2. Check ClickHouse Query Log
        print(f"--- ClickHouse Query Details ---")
        query_log = f"clickhouse-client --query \"SELECT query_duration_ms, read_rows, read_bytes, memory_usage FROM system.query_log WHERE type = 'QueryFinish' AND query LIKE '%{tid}%' ORDER BY event_time DESC LIMIT 1\""
        stdin, stdout, stderr = client.exec_command(query_log)
        print(stdout.read().decode())

        # 3. Count for Recife/PE
        print(f"--- Recife (PE) Statistics ---")
        count_query = "SELECT count() FROM hemn.estabelecimento WHERE uf = 'PE' AND municipio = '2531' AND situacao_cadastral = '02'" # 2531 is Recife in some systems, but let's check
        stdin, stdout, stderr = client.exec_command(f"clickhouse-client --query \"{count_query}\"")
        print(f"Total Recife (PE) records: {stdout.read().decode().strip()}")

        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    diag()
