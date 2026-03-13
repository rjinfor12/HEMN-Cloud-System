import sqlite3
import re

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Name Spacing Check ---")

cursor.execute("SELECT nome_socio FROM socios WHERE nome_socio LIKE 'JOAO %' LIMIT 20")
for r in cursor.fetchall():
    name = r[0]
    multi = "  " in name
    print(f"Name: '{name}' | Multi-space: {multi}")

# Try finding ROGERIO ELIAS with wildcard spaces
name_wild = "ROGERIO%ELIAS%DO%NASCIMENTO%JUNIOR%"
cursor.execute("SELECT nome_socio FROM socios WHERE nome_socio LIKE ? LIMIT 5", [name_wild])
print(f"\nSearching for wildcard name: {name_wild}")
hits = cursor.fetchall()
print(f"Hits: {len(hits)}")
for h in hits:
    print(f"  Result: '{h[0]}'")

conn.close()
