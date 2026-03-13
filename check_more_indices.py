import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

print("=== INDICES EM estabelecimento ===")
cursor.execute("PRAGMA index_list('estabelecimento')")
for idx in cursor.fetchall():
    print(idx)
    cursor.execute(f"PRAGMA index_info('{idx[1]}')")
    print(f"  Colunas: {cursor.fetchall()}")

print("\n=== INDICES EM empresas ===")
cursor.execute("PRAGMA index_list('empresas')")
for idx in cursor.fetchall():
    print(idx)
    cursor.execute(f"PRAGMA index_info('{idx[1]}')")
    print(f"  Colunas: {cursor.fetchall()}")

conn.close()
