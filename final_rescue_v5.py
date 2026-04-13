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

# 1. PARADA TOTAL E PERMANENTE DO DEV
run_cmd(client, "systemctl stop hemn_cloud_dev.service || true")
run_cmd(client, "systemctl disable hemn_cloud_dev.service || true")
run_cmd(client, "fuser -k 8001/tcp || true")
print("Ambiente DEV e porta 8001 limpos definitivamente.")

# 2. CONFIGURAÇÃO NGINX ULTRA-ESPECÍFICA (COM SERVIÇO DE ARQUIVOS ESTÁTICOS DIRETO)
nginx_resgate_v5 = """server {
    listen 80;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    return 301 https://hemnsystem.com.br$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    client_max_body_size 500M;
    
    ssl_certificate /etc/letsencrypt/live/hemnsystem.com.br/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/hemnsystem.com.br/privkey.pem; 
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Força a entrega de arquivos estáticos diretamente pelo Nginx (sem passar pelo Python)
    location /areadocliente/static/ {
        alias /var/www/hemn_cloud/static/;
        autoindex off;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }
}
"""

run_cmd(client, "cat > /etc/nginx/sites-available/hemn_cloud", input_data=nginx_resgate_v5)
run_cmd(client, "nginx -t")
run_cmd(client, "systemctl reload nginx")
print("Nginx configurado para entrega direta de estáticos.")

# 3. REINICIALIZAÇÃO DO SERVIÇO DE PRODUÇÃO
run_cmd(client, "systemctl restart hemn_cloud.service")
print("Serviço oficial reiniciado.")

# 4. CHECAGEM FINAL DE ARQUIVOS
print("Listando arquivos em /var/www/hemn_cloud/static/ novamente:")
out, _, _ = run_cmd(client, "ls -la /var/www/hemn_cloud/static/")
print(out)

client.close()
print("Resgate v5 Finalizado.")
