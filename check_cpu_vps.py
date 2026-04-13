import paramiko

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    
    print("--- TOP 10 CPU Processes ---")
    stdin, stdout, stderr = ssh.exec_command("ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 10")
    print(stdout.read().decode())
    
    print("--- ClickHouse Active Queries ---")
    stdin, stdout, stderr = ssh.exec_command("clickhouse-client --query \"SELECT query_id, elapsed, memory_usage, threads, query FROM system.processes\"")
    print(stdout.read().decode())
    
    ssh.close()
except Exception as e:
    print(e)
