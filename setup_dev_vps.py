import paramiko
import os
import tarfile

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!' # Conforme visto no deploy_vps.py

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: 
        try:
            print("OUT:", out.strip())
        except UnicodeEncodeError:
            print("OUT (Encoded):", out.encode('ascii', 'ignore').decode())
    if err: 
        try:
            print("ERR:", err.strip())
        except UnicodeEncodeError:
            print("ERR (Encoded):", err.encode('ascii', 'ignore').decode())
    return exit_status

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

print("--- Step 1: Preparing Folders ---")
run_cmd(client, 'mkdir -p /var/www/hemn_cloud_dev')

print("--- Step 2: Packaging Dev Files ---")
tar_name = "hemn_dev_deploy.tar.gz"
with tarfile.open(tar_name, "w:gz") as tar:
    # Arquivos principais (mesmos de prod por enquanto)
    files = ["HEMN_Cloud_Server.py", "cloud_engine.py", "index_vps.html", "admin_monitor_vps.html", "static"]
    for f in files:
        if os.path.exists(f):
            tar.add(f)

print("--- Step 3: Uploading to Dev Folder ---")
sftp = client.open_sftp()
sftp.put(tar_name, f"/var/www/hemn_cloud_dev/{tar_name}")

print("--- Step 4: Extracting and Venv ---")
run_cmd(client, f'cd /var/www/hemn_cloud_dev && tar -xzf {tar_name}')
run_cmd(client, 'cd /var/www/hemn_cloud_dev && python3 -m venv venv')
run_cmd(client, 'cd /var/www/hemn_cloud_dev && ./venv/bin/pip install fastapi uvicorn pandas openpyxl python-multipart aiofiles jinja2 xlsxwriter websockets requests pyjwt numpy clickhouse-connect')

print("--- Step 5: ClickHouse Dev Database Clone ---")
# Criar o banco hemn_dev e clonar tabelas críticas
ch_cmds = [
    "CREATE DATABASE IF NOT EXISTS hemn_dev",
    "CREATE TABLE IF NOT EXISTS hemn_dev.empresas AS hemn.empresas",
    "CREATE TABLE IF NOT EXISTS hemn_dev.estabelecimento AS hemn.estabelecimento",
    "CREATE TABLE IF NOT EXISTS hemn_dev.socios AS hemn.socios",
    "CREATE TABLE IF NOT EXISTS hemn_dev.simples AS hemn.simples",
    "CREATE TABLE IF NOT EXISTS hemn_dev.cnae AS hemn.cnae",
    "CREATE TABLE IF NOT EXISTS hemn_dev.municipio AS hemn.municipio",
    "CREATE TABLE IF NOT EXISTS hemn_dev.natureza_juridica AS hemn.natureza_juridica",
    "CREATE TABLE IF NOT EXISTS hemn_dev.qualificacao_socio AS hemn.qualificacao_socio",
    "CREATE TABLE IF NOT EXISTS hemn_dev.leads AS hemn.leads",
    "CREATE TABLE IF NOT EXISTS hemn_dev.leads_v2 AS hemn.leads_v2",
    "CREATE TABLE IF NOT EXISTS hemn_dev.lookup_matrix AS hemn.lookup_matrix",
    "CREATE TABLE IF NOT EXISTS hemn_dev._metadata AS hemn._metadata"
]
# Nota: AS apenas cria o schema. Precisamos do INSERT se quisermos os dados.
# No Clickhouse, INSERT INTO ... SELECT * FROM ... é lento para bilhões de linhas. 
# Mas para tabelas menores ou se o usuário quiser teste real, faremos.
for cmd in ch_cmds:
    run_cmd(client, f'clickhouse-client --query "{cmd}"')

print("--- Step 6: Systemd Service Dev ---")
service_file_content = """[Unit]
Description=HEMN Cloud Dev Server
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/hemn_cloud_dev
Environment="PATH=/var/www/hemn_cloud_dev/venv/bin"
Environment="DB_NAME=hemn_dev"
Environment="ENVIRONMENT=development"
ExecStart=/var/www/hemn_cloud_dev/venv/bin/uvicorn HEMN_Cloud_Server:app --host 127.0.0.1 --port 8001 --proxy-headers
Restart=always

[Install]
WantedBy=multi-user.target"""
sftp.open('/etc/systemd/system/hemn_cloud_dev.service', 'w').write(service_file_content)

print("--- Step 7: Nginx Configuration ---")
sftp.put("vps_nginx.conf", "/etc/nginx/sites-available/hemn_cloud")
run_cmd(client, "ln -sf /etc/nginx/sites-available/hemn_cloud /etc/nginx/sites-enabled/hemn_cloud")
run_cmd(client, "nginx -t && systemctl reload nginx")

print("--- Step 8: SSL with Certbot (Dev) ---")
# Tentar gerar SSL para o dev se o DNS já tiver propagado
run_cmd(client, "certbot --nginx -d dev.hemnsystem.com.br --non-interactive --agree-tos -m rjinfor12@gmail.com")

run_cmd(client, "systemctl daemon-reload")
run_cmd(client, "systemctl enable hemn_cloud_dev.service")
run_cmd(client, "systemctl restart hemn_cloud_dev.service")

sftp.close()
client.close()
print("Dev Environment Setup Script Finished (Partial).")
