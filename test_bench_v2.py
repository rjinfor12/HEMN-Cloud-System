import sqlite3
import time

print("Connecting to DB...")
conn = sqlite3.connect(r"C:\HEMN_SYSTEM_DB\cnpj.db")
conn.execute("PRAGMA journal_mode = WAL;")
conn.execute("PRAGMA temp_store = MEMORY;")
cursor = conn.cursor()

print("Creating temp_search...")
cursor.execute("CREATE TEMP TABLE temp_search (cpf_mask TEXT PRIMARY KEY)")
# Insert 5 fake CPFs and 50 masks
dummy_data = [(f"***{str(i).zfill(6)}**",) for i in range(123450, 128450)]
cursor.executemany("INSERT INTO temp_search VALUES (?)", dummy_data)
print(f"Inserted {len(dummy_data)} search terms.")

print("\n--- Test 1: JOIN socios ---")
start = time.time()
cursor.execute("SELECT s.cnpj_cpf_socio, s.cnpj_basico FROM temp_search t JOIN socios s ON s.cnpj_cpf_socio = t.cpf_mask")
res1 = cursor.fetchall()
print(f"Found {len(res1)} in {time.time() - start:.3f}s")

print("\n--- Test 2: JOIN empresas ---")
start = time.time()
cursor.execute("SELECT t.cpf_mask, e.cnpj_basico FROM temp_search t JOIN empresas e ON e.cnpj_basico = t.cpf_mask")
res2 = cursor.fetchall()
print(f"Found {len(res2)} in {time.time() - start:.3f}s")

print("\nPreparing temp_basics...")
cursor.execute("CREATE TEMP TABLE temp_basics (cpf_mask TEXT, cnpj_basico TEXT)")
cursor.executemany("INSERT INTO temp_basics VALUES (?,?)", res1)
cursor.execute("CREATE INDEX idx_tb_cnpj ON temp_basics(cnpj_basico)")

print("\n--- Test 3: JOIN estabelecimento + empresas ---")
start = time.time()
q3 = """
SELECT 
    m.cpf_mask, e.razao_social, estab.cnpj_basico
FROM temp_basics m INDEXED BY idx_tb_cnpj
JOIN estabelecimento estab INDEXED BY idx_estabelecimento_cnpj_basico ON m.cnpj_basico = estab.cnpj_basico
JOIN empresas e INDEXED BY idx_empresas_cnpj_basico ON m.cnpj_basico = e.cnpj_basico
"""
cursor.execute(q3)
res3 = cursor.fetchall()
print(f"Found {len(res3)} in {time.time() - start:.3f}s")
