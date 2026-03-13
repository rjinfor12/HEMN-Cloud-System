import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect, re

def smart_pad(val):
    clean = re.sub(r'\\D', '', str(val))
    if 9 <= len(clean) <= 10:
        return clean.zfill(11)
    return clean

cpf_raw = '9752279473'
cpf = smart_pad(cpf_raw)
name = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'
mask = f"***{cpf[3:9]}**"

print(f"Raw CPF: {cpf_raw}")
print(f"Padded CPF: {cpf}")
print(f"Mask: {mask}")
print(f"isdigit check: {cpf.isdigit()}, mask isdigit: {mask.isdigit()}")

client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# Simulating what the engine will do
# only digits in patterns – with the bugfix applied
patterns = [cpf]  # mask is excluded because mask.isdigit() == False

patterns_str = ", ".join([f"'{p}'" for p in patterns])

q = f\"\"\"
SELECT DISTINCT e.cnpj_basico, e.razao_social
FROM hemn.empresas e
WHERE multiSearchAny(razao_social, [{patterns_str}])
  AND positionCaseInsensitiveUTF8(razao_social, '{name}') > 0
\"\"\"
res = client.query(q)
print(f"\\nTitanium MEI Scan result: {res.result_rows}")

if res.result_rows:
    basico = res.result_rows[0][0]
    q2 = f\"\"\"
    SELECT ddd1, telefone1, ddd2, telefone2, correio_eletronico, uf, municipio
    FROM hemn.estabelecimento WHERE cnpj_basico = '{basico}'
    \"\"\"
    res2 = client.query(q2)
    print(f"Contact details: {res2.result_rows}")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/final_verify.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/final_verify.py")
print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
print(stderr.read().decode('utf-8'))
client.close()
