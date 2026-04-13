import paramiko

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def check_ch():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        commands = [
            "clickhouse-client --query 'SHOW DATABASES'",
            "clickhouse-client --query 'SHOW TABLES FROM default'",
            "clickhouse-client --query 'SELECT name, engine FROM system.tables WHERE database = \"default\"'",
            "clickhouse-client --query 'SELECT count(*) FROM default.empresas_full' # Se essa tabela existir"
        ]
        
        for cmd in commands:
            print(f"\n> {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err: print(f"STDERR: {err}")
            
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_ch()
