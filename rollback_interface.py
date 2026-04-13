import paramiko
import os
import sys

# VPS Contabo
contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def rollback():
    print(f"Iniciando RESTAURACAO DE EMERGENCIA da Interface na VPS ({contabo_ip})...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(contabo_ip, username=contabo_user, password=contabo_pass)
        
        # 1. Verificar se index_vps.html.bak existe para restaurar
        print("Buscando backup da interface antiga...")
        stdin, stdout, stderr = ssh.exec_command("ls /var/www/hemn_cloud/index_vps.html.bak")
        if stdout.read():
            print("Restaurando backup index_vps.html.bak -> index_vps.html")
            ssh.exec_command("cp /var/www/hemn_cloud/index_vps.html.bak /var/www/hemn_cloud/index_vps.html")
        else:
            # 2. Se não houver backup, vamos tentar voltar o REAL_index_vps.html para index_vps.html
            print("Nao encontrei .bak. Tentando restauracao via cp do static...")
            ssh.exec_command("cp /var/www/hemn_cloud/static/index_vps.html /var/www/hemn_cloud/index_vps.html")
            
        # 3. Limpar possivel conflito de cache do servidor
        print("Reiniciando servicos...")
        ssh.exec_command("systemctl restart hemn_cloud")
        
        print("\n✅ RESTAURACAO CONCLUIDA. Por favor, de um CTRL + F5 no navegador.")
        ssh.close()
        
    except Exception as e:
        print(f"ERRO NA RESTAURACAO: {e}")

if __name__ == "__main__":
    rollback()
