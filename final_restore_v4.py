import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd, input_data=None):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    if input_data:
        stdin.write(input_data)
        stdin.flush()
        stdin.channel.shutdown_write()
    
    status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out, err, status

# 1. PARADA TOTAL DO AMBIENTE DEV (LABORATÓRIO)
run_cmd(client, "systemctl kill hemn_cloud_dev.service || true")
run_cmd(client, "systemctl stop hemn_cloud_dev.service || true")
run_cmd(client, "systemctl disable hemn_cloud_dev.service || true")
run_cmd(client, "fuser -k 8001/tcp || true")
print("Ambiente DEV e porta 8001 limpos.")

# 2. CONFIGURAÇÃO NGINX ULTRA-SIMPLES (SEM HTTP2)
nginx_clean_v4 = """server {
    listen 80;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    return 301 https://hemnsystem.com.br$request_uri;
}

server {
    listen 443 ssl;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    client_max_body_size 500M;
    
    ssl_certificate /etc/letsencrypt/live/hemnsystem.com.br/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/hemnsystem.com.br/privkey.pem; 
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }
}
"""

run_cmd(client, "cat > /etc/nginx/sites-available/hemn_cloud", input_data=nginx_clean_v4)
run_cmd(client, "nginx -t")
run_cmd(client, "systemctl reload nginx")
print("Nginx simplificado para produção.")

# 3. REINICIALIZAÇÃO LIMPA DA PRODUÇÃO
run_cmd(client, "systemctl restart hemn_cloud.service")
print("Serviço oficial reiniciado.")

# 4. PESQUISA FINAL - Onde diabos está o arquivo de login?
print("Pesquisando por qualquer .js na pasta estática de produção:")
out, err, _ = run_cmd(client, "ls -R /var/www/hemn_cloud/static/ | grep '.js'")
print("JS Files em static:", out.strip())

client.close()
print("Restauração v4 (Final) Finalizada.")
