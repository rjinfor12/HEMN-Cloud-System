import paramiko, os, sys

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

if len(sys.argv) < 2:
    print("Uso: python upload_vps_fix.py file1 file2 ...")
    sys.exit(1)

files_to_upload = sys.argv[1:]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

sftp = client.open_sftp()
for f in files_to_upload:
    local_path = os.path.abspath(f)
    remote_filename = os.path.basename(f)
    
    # Mapper logic
    if "static" in f:
        remote_path = f"/var/www/hemn_cloud/static/{remote_filename}"
    elif remote_filename == "HEMN_Cloud_Server_VPS.py":
        remote_path = "/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py"
    elif remote_filename == "HEMN_Cloud_Server.py":
        remote_path = "/var/www/hemn_cloud/HEMN_Cloud_Server.py"
    elif remote_filename == "index_vps.html":
        remote_path = "/var/www/hemn_cloud/index_vps.html"
    else:
        remote_path = f"/var/www/hemn_cloud/{remote_filename}"
    
    if os.path.exists(local_path):
        print(f"Uploading {f} -> {remote_path}...")
        sftp.put(local_path, remote_path)
    else:
        print(f"File not found: {f}")

sftp.close()

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

print('=== REINICIANDO SERVICO NO VPS ===')
print(run("systemctl restart hemn_cloud.service"))

client.close()
print('Upload e reinicialização concluídos com sucesso.')
