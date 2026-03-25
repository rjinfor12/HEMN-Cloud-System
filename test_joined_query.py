import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# The complex query that uses BOTH tables
query = """
SELECT e.cnpj_basico, e.razao_social 
FROM hemn.empresas AS e 
INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico 
PREWHERE e.natureza_juridica = '2135' 
WHERE substring(e.razao_social, -11) IN ('12345678901') 
AND estab.uf IN ('SP')
LIMIT 1
"""

print(f"--- TESTING JOINED QUERY ---\n{query}")
stdin, stdout, stderr = client.exec_command(f'clickhouse-client --query "{query}"')
print("Output:")
print(stdout.read().decode())
print("Errors:")
print(stderr.read().decode())
client.close()
