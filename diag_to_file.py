import paramiko

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def get_full_info():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        cmds = {
            "create_estab": "clickhouse-client --query 'SHOW CREATE TABLE hemn.estabelecimento'",
            "create_empresas": "clickhouse-client --query 'SHOW CREATE TABLE hemn.empresas'",
            "ch_usage": "clickhouse-client --query \"SELECT query, query_duration_ms, read_rows, read_bytes, memory_usage FROM system.query_log WHERE type = 'QueryFinish' ORDER BY event_time DESC LIMIT 10\"",
            "top_mem": "ps aux --sort=-%mem | head -n 5"
        }
        
        with open("diag_output.txt", "w", encoding='utf-8') as f:
            for name, cmd in cmds.items():
                stdin, stdout, stderr = client.exec_command(cmd)
                f.write(f"\n=== {name} ===\n")
                f.write(stdout.read().decode())
                f.write(stderr.read().decode())
        
        client.close()
        print("Diagnostic saved to diag_output.txt")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_full_info()
