import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def add_carrier_status_endpoint():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    # Adicionar o endpoint carrier-status logo após a linha do /admin/monitor/stats
    # Vou inserir após a última linha do bloco @app.get("/admin/monitor/stats")
    
    new_endpoint = '''
@app.get("/admin/monitor/carrier-status")
def get_carrier_status(user: dict = Depends(get_current_user)):
    return engine.get_carrier_status()

@app.post("/admin/monitor/carrier-update")
def start_carrier_update(user: dict = Depends(get_current_user)):
    if user["role"] != "ADMIN": raise HTTPException(status_code=403)
    tid = engine.start_carrier_update(username=user["username"])
    return {"task_id": tid}
'''
    
    # Usar sed para inserir após a linha que contém "@app.get(\"/admin/monitor/stats\")"
    # Primeiro, encontrar o número da última linha do bloco stats
    stdin, stdout, stderr = client.exec_command("grep -n '@app.get(\"/admin/monitor/stats\")' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py")
    line_num = stdout.read().decode().strip().split(":")[0]
    print(f"Linha do endpoint stats: {line_num}")
    
    # Encontrar onde o bloco de stats termina (próxima linha com @app)
    stdin, stdout, stderr = client.exec_command(f"awk 'NR>{line_num} && /^@app/{{print NR; exit}}' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py")
    next_endpoint_line = stdout.read().decode().strip()
    print(f"Próximo endpoint na linha: {next_endpoint_line}")
    
    # Inserir as novas rotas antes do próximo endpoint
    insert_line = int(next_endpoint_line) - 1
    
    # Escapar o código para sed
    escaped = new_endpoint.replace("'", "'\\''").replace("\n", "\\n")
    
    # Usar Python no servidor para fazer a inserção de forma segura
    insert_cmd = f'''python3 -c "
lines = open('/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py').readlines()
new_code = '''
    
    # Mais seguro: enviar um script Python para o servidor
    script = '''import sys
lines = open('/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py').readlines()
insert_at = {insert_line}
new_lines = [
    '\\n',
    '@app.get("/admin/monitor/carrier-status")\\n',
    'def get_carrier_status(user: dict = Depends(get_current_user)):\\n',
    '    return engine.get_carrier_status()\\n',
    '\\n',
    '@app.post("/admin/monitor/carrier-update")\\n',
    'def start_carrier_update(user: dict = Depends(get_current_user)):\\n',
    '    if user["role"] != "ADMIN": raise HTTPException(status_code=403)\\n',
    '    tid = engine.start_carrier_update(username=user["username"])\\n',
    '    return {{"task_id": tid}}\\n',
    '\\n',
]
lines[insert_at-1:insert_at-1] = new_lines
with open('/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py', 'w') as f:
    f.writelines(lines)
print("Endpoints inseridos com sucesso")
'''.replace('{insert_line}', str(insert_line))
    
    # Escrever o script no servidor e executar
    sftp = client.open_sftp()
    with sftp.open('/tmp/add_endpoints.py', 'w') as f:
        f.write(script.replace('{insert_line}', str(insert_line)))
    sftp.close()
    
    stdin, stdout, stderr = client.exec_command('python3 /tmp/add_endpoints.py')
    print(stdout.read().decode().strip())
    print(stderr.read().decode().strip())
    
    # Verificar
    stdin, stdout, stderr = client.exec_command("grep -n 'carrier-status\\|carrier-update' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py")
    print("\nEndpoints adicionados:")
    print(stdout.read().decode().strip())
    
    # Reiniciar
    stdin, stdout, stderr = client.exec_command("fuser -k 8000/tcp || true; systemctl reset-failed hemn_cloud; systemctl restart hemn_cloud; sleep 4; systemctl is-active hemn_cloud")
    print("\nStatus:", stdout.read().decode().strip())
    
    # Testar
    stdin, stdout, stderr = client.exec_command("curl -s http://localhost:8000/admin/monitor/carrier-status")
    print("Teste endpoint:", stdout.read().decode().strip()[:200])
    
    client.close()

if __name__ == "__main__":
    add_carrier_status_endpoint()
