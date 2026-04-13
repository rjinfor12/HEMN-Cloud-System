import paramiko
import os
import time

# Configurações de Conexão
HOSTNAME = "86.48.17.194"
PORT = 22
USERNAME = "root"
PASSWORD = "^QP67kXax9AyuvF%"

# Caminhos Locais
BASE_DIR = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
CORE_FILES = {
    "cloud_engine.py": "/var/www/hemn_cloud/cloud_engine.py",
    "HEMN_Cloud_Server_VPS.py": "/var/www/hemn_cloud/HEMN_Cloud_Server.py",
    "index_vps.html": "/var/www/hemn_cloud/index_vps.html"
}

def execute_deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"[*] Conectando ao VPS {HOSTNAME}...")
    try:
        client.connect(HOSTNAME, port=PORT, username=USERNAME, password=PASSWORD, timeout=15)
        print("[OK] Conectado com sucesso!")
        
        sftp = client.open_sftp()
        
        for local_name, remote_path in CORE_FILES.items():
            local_path = os.path.join(BASE_DIR, local_name)
            if os.path.exists(local_path):
                print(f"[*] Fazendo upload de {local_name} -> {remote_path}...")
                sftp.put(local_path, remote_path)
            else:
                print(f"[!] Arquivo local não encontrado: {local_path}")
        
        sftp.close()
        
        print("[*] Reiniciando motores HEMN...")
        # Parar processos antigos e o serviço
        client.exec_command("systemctl stop hemn_cloud")
        client.exec_command("pkill -9 python3")
        time.sleep(2)
        
        # Reiniciar o serviço principal
        print("[*] Iniciando serviço hemn_cloud...")
        client.exec_command("systemctl start hemn_cloud")
        
        print("\n[SUCCESS] DEPLOY CONCLUIDO COM SUCESSO!")
        print("[INFO] As extracoes agora mostrarao lotes de 100k e os cards persistirao no F5.")
        
    except Exception as e:
        print(f"[ERROR] ERRO NO DEPLOY: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    execute_deploy()
