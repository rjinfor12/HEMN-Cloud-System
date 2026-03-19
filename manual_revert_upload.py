import paramiko, os, sys

sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='root', key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# Enviar o arquivo local (que ja esta no 3dd22bd) para a VPS
local_path = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py"
remote_path = "/var/www/hemn_cloud/cloud_engine.py"

print(f"=== ENVIANDO {local_path} PARA {remote_path} ===")
sftp = client.open_sftp()
sftp.put(local_path, remote_path)
sftp.close()

# Reiniciar
print("=== REINICIANDO SERVIÇO ===")
run("systemctl restart hemn_cloud.service")

print("=== VERIFICANDO SE O SERVIÇO SUBIU ===")
print(run("systemctl status hemn_cloud.service | grep Active"))

client.close()
