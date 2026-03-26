import ftplib
import sys

def test_ftp():
    host = "ftp.portabilidadecelular.com"
    port = 2157
    user = "MAYK"
    passwd = "Mayk@2025"
    
    try:
        print(f"Conectando a {host}:{port}...")
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=30)
        print("Conectado. Fazendo login...")
        ftp.login(user, passwd)
        print("Login realizado com sucesso!")
        
        print("\nListando arquivos:")
        files = []
        ftp.retrlines('LIST', files.append)
        for f in files:
            print(f)
            
        ftp.quit()
        return True
    except Exception as e:
        print(f"Erro na conexão FTP: {e}")
        return False

if __name__ == "__main__":
    test_ftp()
