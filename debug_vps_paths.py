import paramiko

def find_remote_html():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # Procurar por arquivos index.html no sistema
        print("Buscando arquivos index.html no VPS (/var/www)...")
        stdin, stdout, stderr = ssh.exec_command('find /var/www -name "index.html"')
        paths = stdout.read().decode().splitlines()
        
        for p in paths:
            print(f"Encontrado: {p}")
            # Ver conteúdo (primeiras linhas ou grep)
            stdin, stdout, stderr = ssh.exec_command(f'grep "REQUISITO: COLUNA" {p}')
            content = stdout.read().decode()
            print(f"  Conteúdo Requisito: {content.strip()}")
            
        ssh.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    find_remote_html()
