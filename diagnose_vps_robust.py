import paramiko
import os

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def run_deep_audit():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        commands = [
            # 1. Verificar logs do serviço para ver se há Tracebacks do Python
            "echo '--- SERVICO LOGS (Ultimos 50) ---'",
            "journalctl -u hemn_cloud -n 50 --no-pager",
            
            # 2. Verificar se o banco ClickHouse 'hemn' e as tabelas reais existem
            "echo '\n--- CLICKHOUSE DATABASES ---'",
            "clickhouse-client --query 'SHOW DATABASES'",
            
            "echo '\n--- CLICKHOUSE TABLES (HEMN) ---'",
            "clickhouse-client --query 'SHOW TABLES FROM hemn' || echo 'Banco HEMN nao encontrado'",
            
            # 3. Verificar permissões das pastas de storage
            "echo '\n--- PERMISSOES ---'",
            "ls -ld /var/www/hemn_cloud/storage",
            
            # 4. Verificar versões das libs principais
            "echo '\n--- LIBS NO VENV ---'",
            "/var/www/hemn_cloud/venv/bin/pip list | grep -E 'pandas|clickhouse|fastapi'"
        ]
        
        for cmd in commands:
            print(f"\nExcuting: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode('utf-8', 'ignore'))
            err = stderr.read().decode('utf-8', 'ignore')
            if err: print(f"ERROR: {err}")
            
        client.close()
    except Exception as e:
        print(f"FAILED TO CONNECT: {e}")

if __name__ == "__main__":
    run_deep_audit()
