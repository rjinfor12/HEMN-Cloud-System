import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

sql_drop = "DROP VIEW IF EXISTS hemn.full_view"
sql_create = """
CREATE VIEW hemn.full_view AS
SELECT 
    e.cnpj_basico,
    e.razao_social,
    est.cnpj_ordem,
    est.cnpj_dv,
    est.matriz_filial,
    est.nome_fantasia,
    est.situacao_cadastral,
    est.data_situacao_cadastral,
    est.motivo_situacao_cadastral,
    est.uf,
    est.municipio,
    est.ddd1,
    est.telefone1,
    est.ddd2,
    est.telefone2,
    est.correio_eletronico,
    est.logradouro,
    est.bairro,
    est.cep,
    concat(e.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) as cnpj_completo
FROM hemn.empresas e
JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
"""

python_script = f"""import clickhouse_connect
client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)
client.command("{sql_drop}")
client.command(\"\"\"{sql_create}\"\"\")
print("View hemn.full_view created successfully.")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/create_view.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/create_view.py")
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
client.close()
