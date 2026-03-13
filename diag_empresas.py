import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

names = [
    "ROGERIO ELIAS DO NASCIMENTO JUNIOR",
    "ADEMIR DE LISBOA CARVALHO",
    "FABIO LUIZ DE SOUSA",
    "GERALDO APARECIDO LOPES",
    "SANDRA APARECIDA RIBEIRO"
]

print("--- Searching in EMPRESAS (razao_social) ---")
for n in names:
    cursor.execute("SELECT razao_social FROM empresas WHERE razao_social LIKE ? LIMIT 3", [f"{n}%"])
    hits = cursor.fetchall()
    print(f"Search '{n}%' -> Hits: {len(hits)}")
    for h in hits:
        print(f"  Found: '{h[0]}'")

conn.close()
