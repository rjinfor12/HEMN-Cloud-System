import paramiko
import os

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

local_prefix = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\data_assets\prefix_anatel.csv"
local_cod = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\data_assets\cod_operadora.csv"

remote_dir = "/var/www/hemn_cloud/data_assets/"

def upload_assets():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    sftp = client.open_sftp()
    
    for local_path, remote_name in [(local_prefix, "prefix_anatel.csv"), (local_cod, "cod_operadora.csv")]:
        remote_path = remote_dir + remote_name
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            print(f"Enviando {remote_name} ({size} bytes)...")
            sftp.put(local_path, remote_path)
            print(f"  -> OK")
        else:
            print(f"  ERRO: {local_path} não encontrado localmente")
    
    sftp.close()
    
    # Verificar e reiniciar o serviço para recarregar os assets
    stdin, stdout, stderr = client.exec_command("ls -lh /var/www/hemn_cloud/data_assets/")
    print("\nArquivos no servidor:")
    print(stdout.read().decode())
    
    # Reiniciar para carregar os CSVs
    stdin, stdout, stderr = client.exec_command("systemctl restart hemn_cloud && sleep 3 && systemctl is-active hemn_cloud")
    print("Status após restart:", stdout.read().decode().strip())
    
    client.close()

if __name__ == "__main__":
    upload_assets()
