import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Test query from the screenshot
query = "SELECT cnpj_basico, razao_social FROM hemn.empresas PREWHERE natureza_juridica = '2135' WHERE substring(razao_social, -11) IN ('12345678901') LIMIT 1"

print(f"--- RUNNING TEST QUERY ---\n{query}")
stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
client.close()
