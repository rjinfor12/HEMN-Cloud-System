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

try:
    with open(log_file, "w") as f:
        f.write("Iniciando processo de transferência SFTP em nuvem (43GB total)...\n")
        
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)
    sftp = client.open_sftp()
    
    for local_path, remote_path in files_to_upload:
        if os.path.exists(local_path):
            with open(log_file, "a") as f:
                f.write(f"\n[{time.strftime('%H:%M:%S')}] Iniciando upload: {os.path.basename(local_path)}\n")
            print(f"Uploading {local_path} -> {remote_path}")
            
            state = {'last_percent': -1}
            def progress_cb(transferred, total):
                percent = int((transferred / total) * 100)
                if percent != state['last_percent'] and percent % 5 == 0:
                    with open(log_file, "a") as f:
                        f.write(f"[{time.strftime('%H:%M:%S')}] {os.path.basename(local_path)} - Progresso: {percent}%\n")
                    state['last_percent'] = percent
                    
            sftp.put(local_path, remote_path, callback=progress_cb)
            
            with open(log_file, "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Finalizado: {os.path.basename(local_path)}\n")
        else:
            with open(log_file, "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] ARQUIVO NÃO ENCONTRADO: {local_path}\n")
                
    # Fix permissions after upload
    client.exec_command('chown -R root:root /var/www/hemn_cloud/*.db')
    client.exec_command('chmod 644 /var/www/hemn_cloud/*.db')
    
    sftp.close()
    client.close()
    with open(log_file, "a") as f:
        f.write(f"\n[{time.strftime('%H:%M:%S')}] ======== TODOS OS UPLOADS FORAM CONCLUÍDOS COM SUCESSO ========\n")
except Exception as e:
    with open(log_file, "a") as f:
        f.write(f"\nERRO CRÍTICO NO SFTP: {str(e)}\n")
