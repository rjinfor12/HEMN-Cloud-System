import ftplib
import os

try:
    ftp = ftplib.FTP()
    ftp.connect("ftp.portabilidadecelular.com", 2157)
    ftp.login("MAYK", "Mayk@2025")
    print("Files:", ftp.nlst())
    try:
        print("Size:", ftp.size("portabilidade.tar.bz2"))
    except:
        print("Size: Error or 0")
    ftp.quit()
except Exception as e:
    print("Error:", e)
