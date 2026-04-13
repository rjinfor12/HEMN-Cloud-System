import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

# Configuração PURA de Produção (Sem Dev)
pure_prod_nginx = """server {
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

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

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

# 1. Sobrescreve Nginx com Configuração PURA de Produção
run_cmd(client, "cat > /etc/nginx/sites-available/hemn_cloud", input_data=pure_prod_nginx)
print("Configuração Nginx de Produção Reaplicada.")

# 2. Valida e Recarrega Nginx
out, err, status = run_cmd(client, "nginx -t")
if status == 0:
    run_cmd(client, "systemctl reload nginx")
    print("Nginx Recarregado com Sucesso.")
else:
    print("Erro na sintaxe do Nginx:", err)

# 3. Reinicia Sistema de Produção
run_cmd(client, "systemctl restart hemn_cloud.service")
print("Serviço de Produção Reiniciado.")

# 4. Checa as permissões da pasta static (Garantir 755)
run_cmd(client, "chmod -R 755 /var/www/hemn_cloud/static/")
run_cmd(client, "chown -R root:root /var/www/hemn_cloud/static/")
print("Permissões de arquivos estáticos corrigidas.")

client.close()
print("Processo de Restauração Finalizado.")
