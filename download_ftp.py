import ftplib

def download_file():
    host = "ftp.portabilidadecelular.com"
    port = 2157
    user = "MAYK"
    passwd = "Mayk@2025"
    file_to_get = "cod_operadora.csv"
    
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port)
        ftp.login(user, passwd)
        with open(file_to_get, 'wb') as f:
            ftp.retrbinary(f"RETR {file_to_get}", f.write)
        ftp.quit()
        print(f"Arquivo {file_to_get} baixado.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    download_file()
