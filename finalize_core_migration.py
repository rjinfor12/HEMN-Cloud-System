import paramiko
import os

# Hostgator (Old)
old_ip = "129.121.45.136"
old_port = 22022
old_user = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

# Contabo (New)
new_ip = "86.48.17.194"
new_user = "root"
new_pass = "^QP67kXax9AyuvF%"

def transfer_database():
    # 1. Pull from Hostgator
    print(f"Connecting to Hostgator ({old_ip})...")
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    old_client = paramiko.SSHClient()
    old_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    old_client.connect(old_ip, port=old_port, username=old_user, pkey=key)
    
    sftp_old = old_client.open_sftp()
    local_db = "hemn_cloud_vps_migrating.db"
    print(f"Downloading hemn_cloud.db to {local_db}...")
    sftp_old.get("/var/www/hemn_cloud/hemn_cloud.db", local_db)
    sftp_old.close()
    old_client.close()
    
    # 2. Push to Contabo
    print(f"Connecting to Contabo ({new_ip})...")
    new_client = paramiko.SSHClient()
    new_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    new_client.connect(new_ip, username=new_user, password=new_pass)
    
    sftp_new = new_client.open_sftp()
    print(f"Uploading {local_db} to Contabo...")
    sftp_new.put(local_db, "/var/www/hemn_cloud/hemn_cloud.db")
    sftp_new.close()
    
    # 3. Create Service
    print("Creating systemd service on Contabo...")
    service_content = f"""[Unit]
Description=HEMN Cloud Server
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/hemn_cloud
Environment="PATH=/var/www/hemn_cloud/venv/bin"
ExecStart=/var/www/hemn_cloud/venv/bin/uvicorn HEMN_Cloud_Server:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open("hemn_cloud.service", "w") as f: f.write(service_content)
    
    # Upload service file and start
    sftp_new_svc = new_client.open_sftp()
    sftp_new_svc.put("hemn_cloud.service", "/etc/systemd/system/hemn_cloud.service")
    sftp_new_svc.close()
    
    new_client.exec_command("systemctl daemon-reload")
    new_client.exec_command("systemctl enable hemn_cloud")
    new_client.exec_command("systemctl start hemn_cloud")
    
    # 4. Nginx Config (Basic Reverse Proxy)
    print("Configuring Nginx...")
    nginx_conf = """server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
    with open("hemn_nginx", "w") as f: f.write(nginx_conf)
    sftp_ng = new_client.open_sftp()
    sftp_ng.put("hemn_nginx", "/etc/nginx/sites-available/hemn_cloud")
    sftp_ng.close()
    
    new_client.exec_command("ln -s /etc/nginx/sites-available/hemn_cloud /etc/nginx/sites-enabled/")
    new_client.exec_command("rm /etc/nginx/sites-enabled/default")
    new_client.exec_command("systemctl restart nginx")
    
    print("Core Migration Complete!")
    new_client.close()

if __name__ == "__main__":
    transfer_database()
