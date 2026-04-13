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

print("--- Versões do Sistema ---")
prod_v = run_cmd(client, "grep 'SYSTEM_VERSION =' /var/www/hemn_cloud/HEMN_Cloud_Server.py")
dev_v = run_cmd(client, "grep 'SYSTEM_VERSION =' /var/www/hemn_cloud_dev/HEMN_Cloud_Server.py")
print(f"Prod: {prod_v}")
print(f"Dev : {dev_v}")

print("\n--- Checagem de Diretórios ---")
print("Prod Files:", run_cmd(client, "ls -F /var/www/hemn_cloud/ | head -n 5"))
print("Dev Files :", run_cmd(client, "ls -F /var/www/hemn_cloud_dev/ | head -n 5"))

print("\n--- Nginx Header Check ---")
print(run_cmd(client, "curl -sI https://hemnsystem.com.br/areadocliente/ | grep -E 'HTTP|Server'"))
print(run_cmd(client, "curl -sI https://dev.hemnsystem.com.br/areadocliente/ | grep -E 'HTTP|Server'"))

client.close()
