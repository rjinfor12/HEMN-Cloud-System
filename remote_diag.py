import paramiko
import os

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def run_diag():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        commands = [
            "echo '--- CPU and LOAD ---'",
            "uptime",
            "nproc",
            "echo '--- DISK USAGE ---'",
            "df -h /",
            "echo '--- TABLE STRUCTURES ---'",
            "clickhouse-client --query 'SHOW CREATE TABLE hemn.estabelecimento'",
            "clickhouse-client --query 'SHOW CREATE TABLE hemn.empresas'",
            "echo '--- PARTITION INFO ---'",
            "clickhouse-client --query \"SELECT partition, name, active, formatReadableSize(bytes_on_disk) as size FROM system.parts WHERE database = 'hemn' AND table = 'estabelecimento' LIMIT 10\"",
            "echo '--- RECENT QUERY PERFORMANCE ---'",
            "clickhouse-client --query \"SELECT query, query_duration_ms, read_rows, read_bytes, memory_usage FROM system.query_log WHERE type = 'QueryFinish' AND query LIKE '%SELECT%FROM%hemn.estabelecimento%' ORDER BY event_time DESC LIMIT 5\""
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print(out)
            if err: print(f"ERR: {err}")
            
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_diag()
