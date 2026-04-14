import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=username, password=password, timeout=10)

# Testar se o backend responde
stdin, stdout, stderr = client.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/areadocliente/version')
print("HTTP Status:", stdout.read().decode().strip())

# Verificar se a porta esta aberta
stdin, stdout, stderr = client.exec_command('ss -tlnp | grep 8000')
print("Porta 8000:", stdout.read().decode().strip())

# Verificar logs mais recentes (pós-start)
stdin, stdout, stderr = client.exec_command('journalctl -u hemn_cloud -n 5 --no-pager')
print("Logs recentes:")
print(stdout.read().decode().strip())

client.close()
