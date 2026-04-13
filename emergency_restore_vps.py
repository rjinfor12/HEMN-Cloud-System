import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

nginx_restore_conf = """server {
    listen 80;
    server_name www.hemnsystem.com.br hemnsystem.com.br dev.hemnsystem.com.br;
    
    if ($host = dev.hemnsystem.com.br) {
        return 301 https://$host$request_uri;
    }
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

server {
    listen 443 ssl;
    server_name dev.hemnsystem.com.br;
    client_max_body_size 500M;

    ssl_certificate /etc/letsencrypt/live/dev.hemnsystem.com.br/fullchain.pem; 
    ssl_certificate_key /etc/letsencrypt/live/dev.hemnsystem.com.br/privkey.pem; 
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8001;
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
    
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: print("OUT:", out.strip())
    if err: print("ERR:", err.strip())
    return out, err

# Aplica a restauração do Nginx
run_cmd(client, "cat > /etc/nginx/sites-available/hemn_cloud", input_data=nginx_restore_conf)
run_cmd(client, "nginx -t")
run_cmd(client, "systemctl reload nginx")

# Reinicia serviço de produção limpo
run_cmd(client, "systemctl restart hemn_cloud.service")

client.close()
print("Restauração de Emergência Finalizada.")
