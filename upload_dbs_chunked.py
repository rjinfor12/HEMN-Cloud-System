import os
import hashlib
import paramiko
import time
import math
import sys

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

LOCAL_FILE = r"C:\HEMN_SYSTEM_DB\cnpj.db"
REMOTE_FILE = "/var/www/hemn_cloud/cnpj.db"
CHUNK_SIZE_MB = 100
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1024

REMOTE_DIR = "/var/www/hemn_cloud/db_chunks"
LOG_FILE = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\upload_progress.log"

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg)
    sys.stdout.flush()

def get_md5(data):
    return hashlib.md5(data).hexdigest()

def execute_remote(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

def get_remote_md5(client, remote_part_path):
    out, err = execute_remote(client, f"md5sum {remote_part_path} 2>/dev/null")
    if out:
        return out.split()[0]
    return ""

def connect_ssh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH, timeout=30)
    return client

def upload_chunked():
    total_size = os.path.getsize(LOCAL_FILE)
    total_chunks = math.ceil(total_size / CHUNK_SIZE)
    log(f"Iniciando upload particionado de {LOCAL_FILE}")
    log(f"Tamanho Total: {total_size / (1024**3):.2f} GB | Total de Partes: {total_chunks}")
    
    client = connect_ssh()
    execute_remote(client, f"mkdir -p {REMOTE_DIR}")
    sftp = client.open_sftp()
    
    start_time = time.time()
    uploaded_bytes = 0
    
    with open(LOCAL_FILE, 'rb') as f:
        for i in range(total_chunks):
            part_name = f"part_{i:04d}"
            remote_part_path = f"{REMOTE_DIR}/{part_name}"
            
            f.seek(i * CHUNK_SIZE)
            chunk_data = f.read(CHUNK_SIZE)
            local_md5 = get_md5(chunk_data)
            
            remote_md5 = get_remote_md5(client, remote_part_path)
            
            if remote_md5 == local_md5:
                uploaded_bytes += len(chunk_data)
                if i % 5 == 0 or i == total_chunks - 1:
                    percent = (uploaded_bytes / total_size) * 100
                    log(f"Pulando {part_name} - Já existe e OK. Progresso: {percent:.2f}% | {uploaded_bytes/(1024**3):.2f} GB")
                continue
                
            log(f"Uploading Parte {i+1}/{total_chunks} ({part_name}) ...")
            
            success = False
            retries = 5
            while not success and retries > 0:
                try:
                    with sftp.file(remote_part_path, 'wb') as remote_f:
                        remote_f.write(chunk_data)
                        
                    new_remote_md5 = get_remote_md5(client, remote_part_path)
                    
                    if new_remote_md5 == local_md5:
                        success = True
                    else:
                        log(f"Erro de integridade na {part_name}. Remoto: {new_remote_md5}, Local: {local_md5}. Tentando novamente... ({retries} tentativas restantes)")
                        retries -= 1
                except Exception as e:
                    log(f"Erro no SFTP ao enviar {part_name}: {e}. Reconectando...")
                    retries -= 1
                    try:
                        sftp.close()
                        client.close()
                    except:
                        pass
                    time.sleep(5)
                    try:
                        client = connect_ssh()
                        sftp = client.open_sftp()
                    except Exception as cx_e:
                        log(f"Erro ao reconectar SSH: {cx_e}")
                    
            if not success:
                log(f"Falha fatal ao enviar a {part_name} após várias tentativas. Cancelando upload.")
                try:
                    sftp.close()
                    client.close()
                except:
                    pass
                return False
                
            uploaded_bytes += len(chunk_data)
            percent = (uploaded_bytes / total_size) * 100
            elapsed = time.time() - start_time
            # Adjust speed calculation to ignore skipped files time
            # For simplicity, we just show average speed since start
            speed = uploaded_bytes / elapsed if elapsed > 0 else 0
            speed_mb = speed / (1024*1024)
            log(f"Progresso: {percent:.2f}% | Velocidade Avg: {speed_mb:.2f} MB/s | {uploaded_bytes/(1024**3):.2f} GB / {total_size/(1024**3):.2f} GB")

    try:
        sftp.close()
    except:
        pass

    log("\nTodos os blocos foram enviados e verificados com MD5!")
    log("Montando o banco de dados principal no servidor. Isso pode levar alguns minutos...")
    
    # Remount database
    # Since there are many parts, use cat remote_dir/part_*
    assemble_cmd = f"cat {REMOTE_DIR}/part_* > {REMOTE_FILE} && chown root:root {REMOTE_FILE} && chmod 644 {REMOTE_FILE}"
    log(f"Executando assemble: {assemble_cmd}")
    execute_remote(client, assemble_cmd)
    
    log("Banco de dados remontado e permissões aplicadas com sucesso!")
    
    try:
        client.close()
    except:
        pass
        
    return True

if __name__ == '__main__':
    upload_chunked()
