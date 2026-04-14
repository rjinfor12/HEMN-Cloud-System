import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def verify_full_flow():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    commands = [
        # 1. Verificar se após o login, recoverActiveTasks + pollTasks são chamadas
        ("Login flow (3125-3135)",
         "sed -n '3125,3140p' /var/www/hemn_cloud/index_vps.html"),
         
        # 2. Verificar startTask com o fix
        ("startTask com fix (5120-5155)",
         "sed -n '5120,5160p' /var/www/hemn_cloud/index_vps.html"),
        
        # 3. Ver se existem tasks/active nos logs AGORA (após restart)
        ("Logs recentes",
         "journalctl -u hemn_cloud -n 20 --no-pager --since '2 min ago'"),
    ]
    
    for title, cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        err = stderr.read().decode('utf-8', 'ignore').strip()
        result = out or err or "(vazio)"
        print(f"\n[{title}]")
        print(result)
    
    client.close()

if __name__ == "__main__":
    verify_full_flow()
