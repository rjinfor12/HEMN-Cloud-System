import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

print("--- INDEXES IN 'empresas' ---")
cursor.execute("PRAGMA index_list('empresas')")
print(cursor.fetchall())

print("\n--- INDEXES IN 'socios' ---")
cursor.execute("PRAGMA index_list('socios')")
print(cursor.fetchall())

print("\n--- INDEXES IN 'estabelecimento' ---")
cursor.execute("PRAGMA index_list('estabelecimento')")
print(cursor.fetchall())

conn.close()
