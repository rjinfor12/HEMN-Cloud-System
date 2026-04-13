import paramiko

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

print("--- Buscando referências a 'main.js' no HTML de Produção ---")
search_cmd = 'grep -r "main.js" /var/www/hemn_cloud/'
print(run_cmd(client, search_cmd))

print("\n--- Checando conteúdo de index_vps.html (primeiros/últimos scripts) ---")
print(run_cmd(client, 'grep "<script" /var/www/hemn_cloud/index_vps.html | head -n 30'))

print("\n--- Conferindo se o STATIC_DIR no Servidor reflete os arquivos reais ---")
# Simula a lógica do servidor para encontrar STATIC_DIR
print("Arquivos em /var/www/hemn_cloud/static/:")
print(run_cmd(client, 'ls -1 /var/www/hemn_cloud/static/'))

client.close()
