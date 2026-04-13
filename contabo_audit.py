import paramiko

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def check_env():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    commands = [
        "ls -la /var/lib/clickhouse",
        "dpkg -l | grep clickhouse",
        "which clickhouse",
        "which clickhouse-server",
        "systemctl list-units --type=service | grep clickhouse",
        "mkdir -p /var/www/hemn_cloud/storage"
    ]
    
    print("--- Contabo Environment Audit ---")
    for cmd in commands:
        print(f"\n[EXEC] {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
        
    client.close()

if __name__ == "__main__":
    check_env()
