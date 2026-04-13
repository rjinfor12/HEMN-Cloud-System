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

print("--- AUDITORIA DE ARQUIVOS INDEX ---")
# 1. Checa as duas versões de index_vps.html
vps_root_index = "/var/www/hemn_cloud/index_vps.html"
vps_static_index = "/var/www/hemn_cloud/static/index_vps.html"

ls_results = run_cmd(client, f"ls -l {vps_root_index} {vps_static_index}")
print("Arquivos encontrados:\n", ls_results)

# 2. Verifica se a versão da raiz (Mar 28) tem o erro de carregar main.js
grep_root = run_cmd(client, f"grep 'main.js' {vps_root_index}")
print(f"Referência main.js no root (Mar 28): {'SIM' if grep_root else 'NÃO'}")

# 3. Verifica se a versão da pasta static (Mar 25) tem a referência
grep_static = run_cmd(client, f"grep 'main.js' {vps_static_index}")
print(f"Referência main.js no static (Mar 25): {'SIM' if grep_static else 'NÃO'}")

# 4. ROLLBACK SE NECESSÁRIO
if grep_root and not grep_static:
    print("\n[ROLLBACK] Restaurando versão de 25 de Março (Mar 25) para a raiz de produção...")
    run_cmd(client, f"cp {vps_static_index} {vps_root_index}")
    print("Rollback finalizado.")
elif not grep_root:
    print("\nO problema NÃO é a referência ao main.js no index_vps.html da raiz.")
    # Talvez o backend esteja servindo index.html em vez de index_vps.html?
    vps_index_html = "/var/www/hemn_cloud/index.html"
    grep_html = run_cmd(client, f"grep 'main.js' {vps_index_html}")
    if grep_html:
        print("[ROLLBACK] O index.html tem main.js. Substituindo por index_vps.html funcional.")
        run_cmd(client, f"cp {vps_static_index} {vps_root_index}")
        run_cmd(client, f"cp {vps_static_index} {vps_index_html}")
        print("Substituição finalizada.")

# 5. Reinicia o serviço para validar
run_cmd(client, "systemctl restart hemn_cloud.service")
print("\nServiço reiniciado. Pronto para verificação visual.")

client.close()
