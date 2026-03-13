import sqlite3
import unicodedata

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Search with accent
name_accent = "JOAO"
cursor.execute("SELECT nome_socio FROM socios WHERE nome_socio LIKE ? LIMIT 10", [f"{name_accent}%"])
hits = cursor.fetchall()
print(f"--- Search for {name_accent}% ---")
for h in hits:
    print(f"  DB Name: '{h[0]}' | Normalized: '{remove_accents(h[0])}'")

# 2. Search for JOÃO
name_accent2 = "JOÃO"
cursor.execute("SELECT nome_socio FROM socios WHERE nome_socio LIKE ? LIMIT 10", [f"{name_accent2}%"])
hits2 = cursor.fetchall()
print(f"\n--- Search for {name_accent2}% ---")
for h in hits2:
    print(f"  DB Name: '{h[0]}' | Normalized: '{remove_accents(h[0])}'")

conn.close()
