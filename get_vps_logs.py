import paramiko
import sys

def get_logs():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # Obter processos do ClickHouse
        stdin, stdout, stderr = ssh.exec_command("clickhouse-client -q 'SELECT query_id, user, elapsed, query FROM system.processes'")
        print("--- CLICKHOUSE PROCESSLIST ---")
        print(stdout.read().decode('utf-8'))
        
        # Logs do serviço (últimas 20 linhas)
        stdin, stdout, stderr = ssh.exec_command('journalctl -u hemn_cloud.service -n 20 --no-pager')
        print("--- SERVICE LOGS ---")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_logs()
