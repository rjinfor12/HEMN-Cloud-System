import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

name = "JOAO DA SILVA"
print(f"--- Coverage for {name} ---")

cursor.execute("SELECT cnpj_basico FROM socios WHERE nome_socio LIKE ? LIMIT 50", [f"{name}%"])
basics = [r[0] for r in cursor.fetchall()]

active_count = 0
tel_count = 0

for b in basics:
    cursor.execute("SELECT situacao_cadastral, ddd1, telefone1, ddd2, telefone2 FROM estabelecimento WHERE cnpj_basico = ? LIMIT 1", [b])
    res = cursor.fetchone()
    if res:
        sit, d1, t1, d2, t2 = res
        is_active = str(sit).zfill(2) == '02'
        has_tel = bool(str(t1).strip() or str(t2).strip())
        if is_active: active_count += 1
        if is_active and has_tel: tel_count += 1

print(f"Total Basics: {len(basics)}")
print(f"Active Companies: {active_count}")
print(f"Active with Phone: {tel_count}")

conn.close()
