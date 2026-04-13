import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='ignore').strip()

print("--- BUSCANDO 'main.js' EM TODOS OS ARQUIVOS DE /var/www/hemn_cloud ---")
# Procura recursivamente por "main.js" em arquivos de texto
print(run_cmd(client, "grep -r 'main.js' /var/www/hemn_cloud/"))

print("\n--- BUSCANDO QUALQUER ARQUIVO .js NO SERVIDOR INTEIRO ---")
print(run_cmd(client, "find /var/www/hemn_cloud/ -name '*.js'"))

print("\n--- ANALISANDO O CONTEÚDO DE index_vps.html (PRODUÇÃO) ---")
# Vamos ler os primeiros 5000 caracteres para ver o cabeçalho
html_content = run_cmd(client, "head -c 5000 /var/www/hemn_cloud/index_vps.html")
if 'main.js' in html_content:
    print("ENCONTRADO main.js no index_vps.html!")
else:
    print("NÃO encontrado main.js nos primeiros 5000 bytes do index_vps.html.")

print("\n--- ANALISANDO O CONTEÚDO DE HEMN_Cloud_Server.py (PRODUÇÃO) ---")
# Checa se o FastAPI está servindo main.js dinamicamente
print(run_cmd(client, "grep 'main.js' /var/www/hemn_cloud/HEMN_Cloud_Server.py"))

client.close()
