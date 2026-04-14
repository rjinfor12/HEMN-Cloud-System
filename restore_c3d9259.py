import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def restore_and_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    commands = [
        # 0. Fix git safe directory
        ("Fix git safe", "git config --global --add safe.directory /var/www/hemn_cloud"),
        # 1. Restaurar tudo ao commit c3d9259
        ("Restaurar c3d9259", "cd /var/www/hemn_cloud && git reset --hard c3d9259"),
        # 2. Confirmar que estamos no commit certo
        ("Commit atual", "cd /var/www/hemn_cloud && git log --oneline -1"),
        # 3. Confirmar que não há diferenças
        ("Status limpo", "cd /var/www/hemn_cloud && git status --short"),
        # 4. Aplicar a correção do CloudEngine
        ("Corrigir CloudEngine", "sed -i 's/engine = CloudEngine(DB_PATH)/engine = CloudEngine(db_path=DB_PATH)/' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py"),
        # 5. Confirmar a correção
        ("Verificar correção", "grep 'engine = CloudEngine' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py"),
        # 6. Reiniciar o serviço
        ("Parar serviço", "systemctl stop hemn_cloud"),
        ("Matar porta 8000", "fuser -k 8000/tcp || true"),
        ("Resetar falhas", "systemctl reset-failed hemn_cloud"),
        ("Iniciar serviço", "systemctl start hemn_cloud"),
        ("Aguardar", "sleep 4"),
        # 7. Verificar
        ("Status serviço", "systemctl is-active hemn_cloud"),
        ("Teste HTTP", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/"),
    ]
    
    for title, cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        err = stderr.read().decode('utf-8', 'ignore').strip()
        result = out or err or "OK"
        print(f"  [{title}] -> {result}")
    
    client.close()

if __name__ == "__main__":
    restore_and_fix()
