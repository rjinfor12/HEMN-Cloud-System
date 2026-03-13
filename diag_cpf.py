import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Sample CPF/CNPJ from socios ---")
cursor.execute("SELECT cnpj_cpf_socio FROM socios WHERE length(cnpj_cpf_socio) > 0 LIMIT 10")
for r in cursor.fetchall():
    print(f"Data: '{r[0]}'")

conn.close()
