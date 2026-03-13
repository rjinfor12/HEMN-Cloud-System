import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. See real data for a match we know exists
name = "JOAO DA SILVA"
print(f"--- Data for {name} ---")
cursor.execute("SELECT nome_socio, cnpj_cpf_socio FROM socios WHERE nome_socio LIKE ? LIMIT 5", [f"{name}%"])
for r in cursor.fetchall():
    print(f"Name: '{r[0]}' | CPF/CNPJ: '{r[1]}'")

# 2. Try to find the pattern for masking
print("\n--- Masking logic check ---")
cursor.execute("SELECT cnpj_cpf_socio FROM socios WHERE cnpj_cpf_socio LIKE '***%' LIMIT 5")
for r in cursor.fetchall():
    print(f"Masked Data: '{r[0]}'")

conn.close()
