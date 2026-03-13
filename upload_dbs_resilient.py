import paramiko
import os
import time

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

files_to_upload = [
    (r"C:\HEMN_SYSTEM_DB\hemn_carrier.db", "/var/www/hemn_cloud/hemn_carrier.db"),
    (r"C:\HEMN_SYSTEM_DB\cnpj.db", "/var/www/hemn_cloud/cnpj.db")
]

log_file = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\upload_progress.log"

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg)

def robust_upload(sftp, local_path, remote_path):
    local_size = os.path.getsize(local_path)
    remote_size = 0
    try:
        remote_size = sftp.stat(remote_path).st_size
    except IOError:
        remote_size = 0

    if remote_size >= local_size:
        log(f"{os.path.basename(local_path)} - Arquivo ja parece estar 100% no servidor.")
        return True

    log(f"Iniciando/Retomando {os.path.basename(local_path)}: local={local_size}, remote={remote_size}")
    
    with open(local_path, 'rb') as local_file:
        local_file.seek(remote_size)
        with sftp.file(remote_path, 'a') as remote_file:
            chunk_size = 1024 * 1024 * 10 # 10 MB chunks
            transferred = remote_size
            last_percent = int((transferred / local_size) * 100)
            
            while True:
                data = local_file.read(chunk_size)
                if not data:
                    break
                remote_file.write(data)
                transferred += len(data)
                percent = int((transferred / local_size) * 100)
                if percent > last_percent:
                    log(f"{os.path.basename(local_path)} - Progresso: {percent}% ({transferred/(1024**3):.2f} GB / {local_size/(1024**3):.2f} GB)")
                    last_percent = percent
    return True

with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"[{time.strftime('%H:%M:%S')}] Iniciando Upload Resiliente (43GB total)...\n")

for local_path, remote_path in files_to_upload:
    if os.path.exists(local_path):
        success = False
        attempts = 0
        while not success and attempts < 100:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host, port=port, username=user, key_filename=key_path, timeout=30)
                sftp = client.open_sftp()
                
                success = robust_upload(sftp, local_path, remote_path)
                
                sftp.close()
                client.close()
            except Exception as e:
                attempts += 1
                log(f"Conexão caiu! Re-tentando em 5 segundos... (Erro: {e})")
                time.sleep(5)
    else:
        log(f"ARQUIVO NAO ENCONTRADO: {local_path}")
        
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)
    client.exec_command('chown -R root:root /var/www/hemn_cloud/*.db')
    client.exec_command('chmod 644 /var/www/hemn_cloud/*.db')
    client.close()
    log("======== TODOS OS UPLOADS FORAM CONCLUIDOS COM SUCESSO ========")
except:
    pass
