import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

local_db = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"
remote_db = "/var/www/hemn_cloud/hemn_cloud.db"

try:
    print(f"Iniciando RESTAURAÇÃO do banco de dados de usuários...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)
    
    sftp = client.open_sftp()
    
    # 1. Backup do banco atual no servidor (por segurança)
    print("Criando backup de segurança no servidor...")
    client.exec_command(f'cp {remote_db} {remote_db}.bak_{int(os.path.getmtime(local_db))}')
    
    # 2. Upload do banco corrigido
    print(f"Fazendo upload do banco local (com logins recuperados) -> {remote_db}")
    sftp.put(local_db, remote_db)
    
    # 3. Ajustar permissões
    client.exec_command(f'chown root:root {remote_db}')
    client.exec_command(f'chmod 644 {remote_db}')
    
    # 4. Reiniciar serviço para garantir que pegue o novo banco
    print("Reiniciando serviço HEMN Cloud...")
    client.exec_command('systemctl restart hemn_cloud.service')
    
    sftp.close()
    client.close()
    print("\n✓ LOGINS RESTAURADOS COM SUCESSO NO SERVIDOR!")
    
except Exception as e:
    print(f"\n❌ ERRO NA RESTAURAÇÃO: {e}")
