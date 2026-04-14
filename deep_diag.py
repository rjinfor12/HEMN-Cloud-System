import paramiko
import json

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def deep_diagnosis():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    commands = [
        # 1. Tarefa ativa no banco agora
        ("Tarefas ativas agora", 
         "sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT id, module, status, progress, message FROM background_tasks WHERE status IN ('QUEUED','PROCESSING') ORDER BY created_at DESC LIMIT 5;\""),
        
        # 2. Tarefa 134582
        ("Task 134582", 
         "sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT id, module, status, progress, message FROM background_tasks WHERE id LIKE '134582%' ORDER BY created_at DESC LIMIT 3;\""),
        
        # 3. Testar o endpoint /tasks/active como o frontend faria
        ("Endpoint tasks/active (logs)", 
         "journalctl -u hemn_cloud -n 5 --no-pager"),
        
        # 4. Ver se o serviço está rodando
        ("Serviço", "systemctl is-active hemn_cloud"),
        
        # 5. Ver como startTask renderiza o card - procurar a função renderTaskCard
        ("renderTaskCard", 
         "grep -n 'renderTaskCard\\|createTaskCard\\|task-\\${' /var/www/hemn_cloud/index_vps.html | head -15"),
        
        # 6. Ver se pollTasks está sendo chamada pela startTask
        ("startTask chama pollTasks", 
         "grep -n -A 40 'if (data.task_id)' /var/www/hemn_cloud/index_vps.html | head -50"),
        
        # 7. Verificar se o fix do frontend foi aplicado corretamente
        ("Fix verificação", 
         "grep -n 'Fallback: try matching by prefix' /var/www/hemn_cloud/index_vps.html"),
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
    deep_diagnosis()
