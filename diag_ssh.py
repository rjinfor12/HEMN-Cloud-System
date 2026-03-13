import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect

try:
    client = clickhouse_connect.get_client(
        host='localhost', 
        username='default', 
        password='', 
        port=8123
    )

    query = '''
    SELECT s.nome_socio, s.cnpj_cpf_socio, e.razao_social, e.cnpj_basico
    FROM hemn.socios s 
    JOIN hemn.empresas e ON s.cnpj_basico = e.cnpj_basico
    WHERE s.cnpj_cpf_socio = '***522794**'
    LIMIT 20
    '''
    
    res = client.query(query)
    print("Found {} matches:".format(len(res.result_rows)))
    for row in res.result_rows:
        print(row)
        
except Exception as e:
    print("Error: " + str(e))
"""

# Write script to remote file
sftp = client.open_sftp()
with sftp.file('/tmp/diag_ch.py', 'w') as f:
    f.write(python_script)
sftp.close()

cmd = "/var/www/hemn_cloud/venv/bin/python /tmp/diag_ch.py"
stdin, stdout, stderr = client.exec_command(cmd)

print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
