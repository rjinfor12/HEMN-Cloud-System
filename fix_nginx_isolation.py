import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

new_nginx_conf = """server {
    listen 80;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    return 301 https://hemnsystem.com.br$request_uri;
}

server {
    listen 80;
    server_name dev.hemnsystem.com.br;
    return 301 https://dev.hemnsystem.com.br$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dev.hemnsystem.com.br;
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ssl_certificate /etc/letsencrypt/live/dev.hemnsystem.com.br/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/dev.hemnsystem.com.br/privkey.pem; 
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    listen 443 ssl http2 default_server;
    server_name www.hemnsystem.com.br hemnsystem.com.br;
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ssl_certificate /etc/letsencrypt/live/hemnsystem.com.br/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/hemnsystem.com.br/privkey.pem; 
    include /etc/letsencrypt/options-ssl-nginx.conf; 
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; 
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
    
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: print("OUT:", out.strip())
    if err: print("ERR:", err.strip())
    return out, err

# Aplica a nova configuração do Nginx (Escrita direta no arquivo como root)
run_cmd(client, "cat > /etc/nginx/sites-available/hemn_cloud", input_data=new_nginx_conf)

# Testa e reinicia
run_cmd(client, "nginx -t")
run_cmd(client, "systemctl reload nginx")

client.close()
print("Configuração do Nginx atualizada e isolada.")
