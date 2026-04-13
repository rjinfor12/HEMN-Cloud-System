import paramiko

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def get_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Obter os últimos logs do serviço
        stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 100 --no-pager")
        logs = stdout.read().decode('utf-8', 'ignore')
        print("--- LOGS DO SERVICO ---")
        print(logs)
        
        client.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    get_logs()
