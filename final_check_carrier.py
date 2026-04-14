import paramiko
import json

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def final_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    # 1. Gerar token com username correto "admin"
    token_cmd = '''python3 -c "
import sys
sys.path.insert(0, '/var/www/hemn_cloud')
import jwt
from datetime import datetime, timedelta
SECRET_KEY = 'HEMN_SECRET_2026_STABLE_v2_2'
token = jwt.encode({'sub': 'admin', 'exp': datetime.utcnow() + timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
print(token)
"'''
    stdin, stdout, stderr = client.exec_command(token_cmd)
    token = stdout.read().decode().strip()
    print("[Token OK]:", token[:40] + "...")
    
    # 2. Chamar carrier-status com token válido
    stdin, stdout, stderr = client.exec_command(f"curl -s http://localhost:8000/admin/monitor/carrier-status -H 'Authorization: Bearer {token}'")
    response = stdout.read().decode().strip()
    print("\n[carrier-status response]:", response)
    
    # 3. Buscar referências no index.html servido pelo FastAPI
    stdin, stdout, stderr = client.exec_command(f"curl -s http://localhost:8000/ -H 'Authorization: Bearer {token}' | grep -o 'carrier[^\"]*' | head -20")
    carrier_refs = stdout.read().decode().strip()
    print("\n[Carrier refs no HTML]:", carrier_refs)
    
    # 4. Buscar no index.html e admin_monitor
    stdin, stdout, stderr = client.exec_command("grep -n 'carrier\\|Desconhecida\\|Base da Receita' /var/www/hemn_cloud/index.html /var/www/hemn_cloud/admin_monitor_vps.html 2>/dev/null | head -20")
    print("\n[HTML grep]:", stdout.read().decode().strip())
    
    client.close()

if __name__ == "__main__":
    final_check()
