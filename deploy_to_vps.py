import paramiko
import os
import sys

# Configurações da VPS Contabo
contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

# Arquivos locais corrigidos
local_files = [
    r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py",
    r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\HEMN_Cloud_Server_VPS.py",
    r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\REAL_index_vps.html"
]

remote_dir = "/var/www/hemn_cloud"

def deploy():
    print(f"Deploy para VPS Contabo ({contabo_ip})...")
    
    try:
        # 1. Conectar via SSH
        transport = paramiko.Transport((contabo_ip, 22))
        transport.connect(username=contabo_user, password=contabo_pass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # 2. Upload dos arquivos
        for local_path in local_files:
            filename = os.path.basename(local_path)
            remote_path = os.path.join(remote_dir, filename).replace('\\', '/')
            
            # Caso especial para o HTML
            if "REAL_index_vps.html" in filename:
                remote_path = (remote_dir + "/index_vps.html")
            
            print(f"Enviando {filename} para {remote_path}...")
            sftp.put(local_path, remote_path)
        
        sftp.close()
        
        # 3. Reiniciar Serviço via SSH
        print("Reiniciando servico hemn_cloud na VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(contabo_ip, username=contabo_user, password=contabo_pass)
        
        # Comando para garantir que o processo morra e suba o novo código
        cmd = "systemctl restart hemn_cloud"
        ssh.exec_command(cmd)
        
        # Aguardar um momento e verificar status
        import time
        time.sleep(2)
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active hemn_cloud")
        status = stdout.read().decode().strip()
        
        if status == "active":
            print("DEPLOY CONCLUIDO COM SUCESSO! Sistema Reiniciado.")
        else:
            print(f"AVISO: O servico retornou status: {status}")
            
        ssh.close()
        
    except Exception as e:
        print(f"ERRO NO DEPLOY: {e}")

if __name__ == "__main__":
    deploy()
