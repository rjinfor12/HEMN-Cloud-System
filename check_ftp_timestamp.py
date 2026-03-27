
import ftplib
import datetime

def check_ftp_update():
    host = "ftp.portabilidadecelular.com"
    port = 2157
    user = "MAYK"
    passwd = "Mayk@2025"
    filename = "portabilidade.tar.bz2"
    
    print(f"Conectando ao FTP: {host}:{port}...")
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=15)
        ftp.login(user, passwd)
        
        # Obter timestamp de modificação (MDTM)
        # Nem todos os servidores FTP suportam MDTM, mas vamos tentar.
        try:
            timestamp = ftp.voidcmd(f"MDTM {filename}").split()[1]
            # Formato: YYYYMMDDHHMMSS
            dt = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
            print(f"\n[SUCESSO] Arquivo: {filename}")
            print(f"Data de Modificação: {dt.strftime('%d/%m/%Y %H:%M:%S')} (UTC)")
        except:
            # Fallback: Usar NLST ou LIST e parsear (mais complexo, mas NLST às vezes funciona)
            print("MDTM não suportado. Tentando listagem detalhada...")
            lines = []
            ftp.dir(filename, lines.append)
            if lines:
                print(f"Detalhes: {lines[0]}")
            else:
                print("Não foi possível obter detalhes do arquivo.")

        # Tamanho do arquivo
        size = ftp.size(filename)
        print(f"Tamanho: {size / (1024*1024):.2f} MB")
        
        ftp.quit()
    except Exception as e:
        print(f"\n[ERRO] Falha ao conectar ou ler FTP: {e}")

if __name__ == "__main__":
    check_ftp_update()
