import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

name = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
cpf = "09752279473"

print(f"--- Diagnostic for actual user data ---")
print(f"Target: {name} | CPF: {cpf}")

# Search by CPF
cursor.execute("SELECT cnpj_basico, nome_socio FROM socios WHERE cnpj_cpf_socio = ?", [cpf])
hits_cpf = cursor.fetchall()
print(f"Hits by CPF: {len(hits_cpf)}")
for h in hits_cpf:
    print(f"  CNPJ: {h[0]} | Name in DB: '{h[1]}'")

# Search by Name Prefix
cursor.execute("SELECT cnpj_basico, cnpj_cpf_socio FROM socios WHERE nome_socio LIKE ? LIMIT 5", [f"{name}%"])
hits_name = cursor.fetchall()
print(f"Hits by Name Prefix: {len(hits_name)}")
for h in hits_name:
    print(f"  CNPJ: {h[0]} | CPF in DB: '{h[1]}'")

# Search by Name Contains
cursor.execute("SELECT cnpj_basico FROM socios WHERE nome_socio LIKE ? LIMIT 5", [f"%{name}%"])
hits_contains = cursor.fetchall()
print(f"Hits by Name Contains: {len(hits_contains)}")

conn.close()
