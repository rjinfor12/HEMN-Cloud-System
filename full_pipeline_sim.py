import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

# Full pipeline simulation matching the engine exactly
python_script = """import clickhouse_connect, re, traceback

def smart_pad(val):
    clean = re.sub(r'\\D', '', str(val))
    if 9 <= len(clean) <= 10:
        return clean.zfill(11)
    return clean

# Simulate input as it comes from Excel (zero stripped)
input_data = [
    ('9752279473', 'rogerio elias do nascimento junior'),
]

import unicodedata
def remove_accents(s):
    if not s: return ""
    nfkd = unicodedata.normalize('NFKD', str(s))
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

client = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# Build search tuples
search_tuples = []
for cpf_raw, name_raw in input_data:
    cpf = smart_pad(cpf_raw)
    name = remove_accents(name_raw.upper().strip())
    print(f"Processed CPF: {cpf}, Name: {name}")
    if len(cpf) == 11:
        mask = f"***{cpf[3:9]}**"
        search_tuples.append((cpf, name))
        search_tuples.append((mask, name))
    else:
        search_tuples.append((cpf, ""))

search_tuples = list(set(search_tuples))
print(f"Search tuples: {search_tuples}")

# Create temp tables
client.command("CREATE TABLE IF NOT EXISTS temp_search_SIMTEST (search_term String, target_name String) ENGINE = Memory")
client.command("TRUNCATE TABLE temp_search_SIMTEST")
client.command("CREATE TABLE IF NOT EXISTS temp_basicos_SIMTEST (cnpj_basico String, original_search String) ENGINE = Memory")
client.command("TRUNCATE TABLE temp_basicos_SIMTEST")

# Insert tuples
client.insert('temp_search_SIMTEST', search_tuples, column_names=['search_term', 'target_name'])
print("Inserted into temp_search_SIMTEST")

# Step 1: Socios
client.command(\"\"\"
    INSERT INTO temp_basicos_SIMTEST (cnpj_basico, original_search)
    SELECT DISTINCT s.cnpj_basico, ts.search_term
    FROM hemn.socios s
    JOIN temp_search_SIMTEST ts ON s.cnpj_cpf_socio = ts.search_term
    WHERE ts.target_name = '' OR positionCaseInsensitiveUTF8(s.nome_socio, ts.target_name) > 0
\"\"\")
c1 = client.query("SELECT count() FROM temp_basicos_SIMTEST").result_rows[0][0]
print(f"After Step 1 (socios): {c1} rows")

# Step 2: MEI scan
all_cpfs = list(set(t[0] for t in search_tuples if len(t[0]) == 11 and t[0].isdigit()))
print(f"all_cpfs for MEI scan: {all_cpfs}")
if all_cpfs:
    patterns_str = ", ".join([f"'{c}'" for c in all_cpfs])
    mei_q = f\"\"\"
    INSERT INTO temp_basicos_SIMTEST (cnpj_basico, original_search)
    WITH 
        [{patterns_str}] AS patterns,
        multiSearchFirstIndex(razao_social, patterns) AS p_idx
    SELECT DISTINCT
        e.cnpj_basico,
        patterns[p_idx] AS original_search
    FROM hemn.empresas e
    JOIN temp_search_SIMTEST ts ON ts.search_term = patterns[p_idx]
    WHERE p_idx > 0
      AND (ts.target_name = '' OR positionCaseInsensitiveUTF8(e.razao_social, ts.target_name) > 0)
    \"\"\"
    try:
        client.command(mei_q)
        print("MEI scan done")
    except Exception as ex:
        print(f"MEI SCAN ERROR: {ex}")
        traceback.print_exc()

c2 = client.query("SELECT count() FROM temp_basicos_SIMTEST").result_rows[0][0]
print(f"After Step 2 (MEI): {c2} rows")

# Check what's in temp_basicos
rows = client.query("SELECT * FROM temp_basicos_SIMTEST").result_rows
print(f"temp_basicos content: {rows}")

# Step 3: Final enrichment
if c2 > 0:
    q = \"\"\"
    SELECT tb.original_search, e.razao_social, estab.ddd1, estab.telefone1, estab.correio_eletronico, estab.uf
    FROM temp_basicos_SIMTEST tb
    JOIN hemn.estabelecimento estab ON tb.cnpj_basico = estab.cnpj_basico
    JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
    \"\"\"
    res = client.query(q)
    print(f"Final enrichment: {res.result_rows[:3]}")

# Cleanup
client.command("DROP TABLE IF EXISTS temp_search_SIMTEST")
client.command("DROP TABLE IF EXISTS temp_basicos_SIMTEST")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/full_sim.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/full_sim.py")
print("STDOUT:")
print(stdout.read().decode('utf-8'))
print("STDERR:")
s = stderr.read().decode('utf-8')
if s: print("STDERR:", s)
client.close()
