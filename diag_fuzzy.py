import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Reference check
print("--- Database Reference ---")
try:
    cursor.execute("SELECT * FROM _referencia")
    for r in cursor.fetchall():
        print(f"Ref: {r}")
except:
    print("No _referencia table or erro.")

# 2. Fuzzy search for first few names
names_to_try = [
    "ROGERIO ELIAS",
    "ADEMIR DE LISBOA",
    "FABIO LUIZ",
    "GERALDO APARECIDO",
    "SANDRA APARECIDA"
]

print("\n--- Fuzzy Search (First 2-3 words) ---")
for n in names_to_try:
    cursor.execute("SELECT nome_socio FROM socios WHERE nome_socio LIKE ? LIMIT 3", [f"{n}%"])
    hits = cursor.fetchall()
    print(f"Search '{n}%' -> Hits: {len(hits)}")
    for h in hits:
        print(f"  Found: '{h[0]}'")

conn.close()
