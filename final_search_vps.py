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

print("--- PESQUISA GLOBAL POR main.js ---")
print(run_cmd(client, "find /var/www -name 'main.js'"))

print("\n--- PESQUISA POR REFERÊNCIA NO CÓDIGO ---")
# Procura por "main.js" em qualquer arquivo de texto no servidor
print(run_cmd(client, "grep -r 'main.js' /var/www/hemn_cloud/"))

print("\n--- INSPEÇÃO DO INDEX_VPS.HTML INTEIRO (Sem print) ---")
# Vou apenas checar se a string main.js está nele
res = run_cmd(client, "grep 'main.js' /var/www/hemn_cloud/index_vps.html")
print(f"main.js no index_vps: {'SIM' if res else 'NÃO'}")

print("\n--- STATUS DO BACKEND PORTA 8000 ---")
print(run_cmd(client, "systemctl status hemn_cloud.service | grep Active"))

client.close()
