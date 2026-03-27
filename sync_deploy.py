import paramiko
import os
import tarfile

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')
password = 'ChangeMe123!'

def run_cmd(client, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', 'ignore')
    err = stderr.read().decode('utf-8', 'ignore')
    if out: print("OUT:", out.encode('ascii', 'ignore').decode())
    if err: print("ERR:", err.encode('ascii', 'ignore').decode())
    return exit_status

print(f"Connecting to {host}:{port}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=port, username=user, key_filename=key_path, timeout=10)
except:
    print("Key failed, trying password...")
    client.connect(host, port=port, username=user, password=password)

print("Packaging application files...")
tar_name = "hemn_sync_deploy.tar.gz"
files_to_sync = [
    "HEMN_Cloud_Server.py",
    "cloud_engine.py",
    "index_vps.html",
    "admin_monitor_vps.html",
    "design-system.css",
    ".env"
]

with tarfile.open(tar_name, "w:gz") as tar:
    for f in files_to_sync:
        if os.path.exists(f):
            print(f"Adding {f} to bundle...")
            tar.add(f)
        else:
            print(f"WARNING: File {f} missing!")

print("Uploading bundle to VPS...")
sftp = client.open_sftp()
sftp.put(tar_name, f"/var/www/hemn_cloud/{tar_name}")

print("Extracting and Setting up environment...")
run_cmd(client, f'cd /var/www/hemn_cloud && tar -xzf {tar_name}')

# Ensure dependencies are installed in venv
run_cmd(client, 'cd /var/www/hemn_cloud && ./venv/bin/pip install passlib bcrypt python-dotenv clickhouse-connect')

print("Restarting service...")
run_cmd(client, 'systemctl restart hemn_cloud.service')

print("Sync finished successfully.")
sftp.close()
client.close()
