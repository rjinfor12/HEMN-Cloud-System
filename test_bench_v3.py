import sqlite3
import time

print("Connecting to DB...")
conn = sqlite3.connect(r"C:\HEMN_SYSTEM_DB\cnpj.db")
conn.execute("PRAGMA journal_mode = WAL;")
cursor = conn.cursor()

# 5000 terms
terms = [f"***{str(i).zfill(6)}**" for i in range(123450, 128450)]

print("\n--- Test 4: Chunks of 500 IN socios ---")
start = time.time()
res_socios = []
for i in range(0, len(terms), 500):
    chunk = terms[i:i+500]
    q = f"SELECT cnpj_cpf_socio, cnpj_basico FROM socios WHERE cnpj_cpf_socio IN ({','.join(['?']*len(chunk))})"
    cursor.execute(q, chunk)
    res_socios.extend(cursor.fetchall())
print(f"Found {len(res_socios)} in {time.time() - start:.3f}s")
