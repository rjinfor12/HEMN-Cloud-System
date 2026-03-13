import paramiko
import os
import tarfile

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out: print("OUT:", out.encode('ascii', 'ignore').decode())
    if err: print("ERR:", err.encode('ascii', 'ignore').decode())
    return exit_status

print(f"Connecting to {host}:{port} via key...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

print("Preparing Ubuntu Server...")
run_cmd(client, 'apt-get update')
run_cmd(client, 'DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv sqlite3 nginx htop')
run_cmd(client, 'mkdir -p /var/www/hemn_cloud')

print("Packaging application files...")
tar_name = "hemn_deploy.tar.gz"
with tarfile.open(tar_name, "w:gz") as tar:
    tar.add("HEMN_Cloud_Server.py")
    tar.add("cloud_engine.py")
    if os.path.exists("main_gui.py"): tar.add("main_gui.py")
    if os.path.exists("index.html"): tar.add("index.html")
    if os.path.exists("index_vps.html"): tar.add("index_vps.html")
    if os.path.exists("static"): tar.add("static")
    
print("Uploading bundle to VPS...")
sftp = client.open_sftp()
sftp.put(tar_name, f"/var/www/hemn_cloud/{tar_name}")

print("Extracting and Setting up Python Env...")
run_cmd(client, f'cd /var/www/hemn_cloud && tar -xzf {tar_name}')
run_cmd(client, 'cd /var/www/hemn_cloud && python3 -m venv venv')
run_cmd(client, 'cd /var/www/hemn_cloud && ./venv/bin/pip install fastapi uvicorn pandas openpyxl python-multipart aiofiles jinja2 xlsxwriter websockets requests pyjwt numpy')

# Deploy Nginx Config
if os.path.exists("vps_nginx.conf"):
    print("Uploading Nginx config...")
    sftp.put("vps_nginx.conf", "/etc/nginx/sites-available/hemn_cloud")
    run_cmd(client, "ln -sf /etc/nginx/sites-available/hemn_cloud /etc/nginx/sites-enabled/hemn_cloud")
    # Clean up default if it exists and conflicts
    run_cmd(client, "rm -f /etc/nginx/sites-enabled/default")
    run_cmd(client, "nginx -t && systemctl reload nginx")

run_cmd(client, 'systemctl restart nginx')

service_file = """[Unit]
Description=HEMN Cloud FastAPI Server
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/hemn_cloud
Environment="PATH=/var/www/hemn_cloud/venv/bin"
ExecStart=/var/www/hemn_cloud/venv/bin/uvicorn HEMN_Cloud_Server:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always

[Install]
WantedBy=multi-user.target"""
sftp.open('/etc/systemd/system/hemn_cloud.service', 'w').write(service_file)

run_cmd(client, 'systemctl daemon-reload')
run_cmd(client, 'systemctl enable hemn_cloud.service')
run_cmd(client, 'systemctl restart hemn_cloud.service')

sftp.close()
client.close()
print("Deployment structure finished. Nginx config updated for /.")
