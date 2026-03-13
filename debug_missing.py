import sqlite3
import unicodedata

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

# Test variables for Row 2
cpf_raw = "9752279473"
nome_raw = "rogerio elias do nascimento junior"

cpf_digits = cpf_raw.zfill(11)
cpf_miolo = cpf_digits[3:9]
cpf_mask = f"***{cpf_miolo}**"
nome = remove_accents(nome_raw.upper())

print(f"Buscando: CPF={cpf_digits} | MASK={cpf_mask} | NOME={nome}")

# 1. Buscar na tabela SOCIOS por CPF EXATO
cursor.execute("SELECT * FROM socios WHERE cnpj_cpf_socio = ?", [cpf_digits])
print("\n--- SOCIO CPF EXATO ---")
print(cursor.fetchall())

# 2. Buscar na tabela SOCIOS por MASK
cursor.execute("SELECT * FROM socios WHERE cnpj_cpf_socio = ? LIMIT 20", [cpf_mask])
print("\n--- SOCIO MASK (Amostras) ---")
hits = cursor.fetchall()
for h in hits:
    print(h)

# 3. Buscar na tabela EMPRESAS por nome (MEI)
# Nota: Empresas MEI costumam ter o CPF no final da razão social
search_name = f"{nome}%"
cursor.execute("SELECT * FROM empresas WHERE razao_social LIKE ? LIMIT 5", [search_name])
print("\n--- EMPRESAS NOME LIKE ---")
print(cursor.fetchall())

# 4. Buscar por parte do nome na tabela socios
search_name_part = f"%{nome.split()[0]}%{nome.split()[-1]}%"
cursor.execute("SELECT * FROM socios WHERE nome_socio LIKE ? LIMIT 5", [search_name_part])
print("\n--- SOCIO NOME LIKE ---")
print(cursor.fetchall())

conn.close()
