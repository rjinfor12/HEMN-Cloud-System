import paramiko
import json

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def deep_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    commands = [
        # 1. Fazer login e pegar token
        ("Login", """curl -s -X POST http://localhost:8000/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}'"""),
    ]
    
    # Primeiro pegar o token
    stdin, stdout, stderr = client.exec_command(commands[0][1])
    login_response = stdout.read().decode().strip()
    print(f"[Login] -> {login_response}")
    
    try:
        token = json.loads(login_response).get("token")
    except:
        # Tentar pegar senha do admin do banco
        stdin, stdout, stderr = client.exec_command("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT username, password FROM users WHERE role='ADMIN' LIMIT 3;\"")
        print(f"[Admin users] -> {stdout.read().decode().strip()}")
        
        # Tentar com credenciais do banco
        stdin, stdout, stderr = client.exec_command("sqlite3 /var/www/hemn_cloud/hemn_cloud.db \"SELECT username FROM users LIMIT 5;\"")
        users = stdout.read().decode().strip()
        print(f"[Users] -> {users}")
        client.close()
        return
    
    if token:
        print(f"[Token] -> {token[:30]}...")
        
        # 2. Chamar carrier-status com token
        stdin, stdout, stderr = client.exec_command(f"curl -s http://localhost:8000/admin/monitor/carrier-status -H 'Authorization: Bearer {token}'")
        status_response = stdout.read().decode().strip()
        print(f"\n[carrier-status response] -> {status_response}")
        
        # 3. Ver o que o frontend procura no HTML/JS
        stdin, stdout, stderr = client.exec_command("grep -rn 'carrier-status\\|Base da Receita\\|Desconhecida\\|carrierStatus' /var/www/hemn_cloud/static/ 2>/dev/null | head -20")
        print(f"\n[Frontend references] -> {stdout.read().decode().strip()}")
        
        # 4. Verificar o index.html
        stdin, stdout, stderr = client.exec_command("grep -rn 'carrier-status\\|Base da Receita\\|Desconhecida' /var/www/hemn_cloud/index.html /var/www/hemn_cloud/static/*.html 2>/dev/null | head -20")
        print(f"\n[HTML references] -> {stdout.read().decode().strip()}")
    
    client.close()

if __name__ == "__main__":
    deep_check()
