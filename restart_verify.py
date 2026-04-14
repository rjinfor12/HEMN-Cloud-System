import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def restart_and_verify():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    commands = [
        ("Parar serviço", "systemctl stop hemn_cloud"),
        ("Matar porta", "fuser -k 8000/tcp || true"),
        ("Esperar", "sleep 2"),
        ("Reset", "systemctl reset-failed hemn_cloud"),
        ("Iniciar", "systemctl start hemn_cloud"),
        ("Esperar subir", "sleep 4"),
        ("Status", "systemctl is-active hemn_cloud"),
        ("Teste carrier-status", "curl -s http://localhost:8000/admin/monitor/carrier-status"),
        ("Logs", "journalctl -u hemn_cloud -n 5 --no-pager"),
    ]
    
    for title, cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        err = stderr.read().decode('utf-8', 'ignore').strip()
        result = out or err or "OK"
        print(f"[{title}] -> {result}")
    
    client.close()

if __name__ == "__main__":
    restart_and_verify()
