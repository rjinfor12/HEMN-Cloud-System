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

print("--- PESQUISA POR REFERÊNCIA NO CÓDIGO (grep -r) ---")
# Procura recursivamente por "main.js" dentro de /var/www/hemn_cloud
print(run_cmd(client, "grep -r 'main.js' /var/www/hemn_cloud/"))

print("\n--- PESQUISA POR QUALQUER ARQUIVO .js ---")
print(run_cmd(client, "find /var/www/hemn_cloud/ -name '*.js'"))

print("\n--- ANALISANDO O CONTEÚDO DE HEMN_Cloud_Server.py ---")
# Vamos ver como o FastAPI monta a pasta de estáticos
print(run_cmd(client, "grep 'StaticFiles' /var/www/hemn_cloud/HEMN_Cloud_Server.py"))

client.close()
