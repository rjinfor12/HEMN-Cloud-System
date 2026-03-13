import paramiko, time

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

python_script = """import clickhouse_connect, time

ch = clickhouse_connect.get_client(host='localhost', username='default', password='', port=8123)

# Setup temp tables with Rogerio and some extra made-up CPFs (like a real large file)
ch.command("CREATE TABLE IF NOT EXISTS bm_search (search_term String, target_name String) ENGINE = Memory")
ch.command("TRUNCATE TABLE bm_search")
ch.command("CREATE TABLE IF NOT EXISTS bm_basicos (cnpj_basico String, original_search String) ENGINE = Memory")
ch.command("TRUNCATE TABLE bm_basicos")

# Insert Rogerio + 500 random CPFs to simulate a large file
test_tuples = [('09752279473', 'ROGERIO ELIAS DO NASCIMENTO JUNIOR')]
import random, string
for i in range(500):
    fake_cpf = ''.join([str(random.randint(0,9)) for _ in range(11)])
    test_tuples.append((fake_cpf, ''))

ch.insert('bm_search', test_tuples, column_names=['search_term', 'target_name'])
print(f"Inserted {len(test_tuples)} rows into bm_search")

# NEW single-pass query
t0 = time.time()
q = \"\"\"
INSERT INTO bm_basicos (cnpj_basico, original_search)
WITH extracted AS (
    SELECT
        cnpj_basico,
        razao_social,
        arrayJoin(extractAllGroupsHorizontal(razao_social, '([0-9]{11})')) AS cpf_groups
    FROM hemn.empresas
    WHERE match(razao_social, '[0-9]{11}')
)
SELECT DISTINCT
    ex.cnpj_basico,
    ts.search_term AS original_search
FROM extracted ex
ARRAY JOIN ex.cpf_groups AS extracted_cpf
JOIN bm_search ts ON ts.search_term = extracted_cpf
WHERE length(ts.search_term) = 11
  AND (ts.target_name = '' OR positionCaseInsensitiveUTF8(ex.razao_social, ts.target_name) > 0)
\"\"\"
ch.command(q)
t1 = time.time()
elapsed = t1 - t0

count = ch.query("SELECT count() FROM bm_basicos").result_rows[0][0]
rows = ch.query("SELECT * FROM bm_basicos LIMIT 5").result_rows
print(f"Single-pass completed in {elapsed:.2f}s, found {count} MEIs")
print(f"Sample results: {rows}")

ch.command("DROP TABLE IF EXISTS bm_search")
ch.command("DROP TABLE IF EXISTS bm_basicos")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/bench_single_pass.py', 'w') as f:
    f.write(python_script)
sftp.close()

stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python /tmp/bench_single_pass.py")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err: print("STDERR:", err)
client.close()
