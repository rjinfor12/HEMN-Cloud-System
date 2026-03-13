import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

cnpj_basico = '18528540'
print(f"Buscando estabelecimento para CNPJ Básico: {cnpj_basico}")
cursor.execute("SELECT * FROM estabelecimento WHERE cnpj_basico = ?", [cnpj_basico])
estab = cursor.fetchone()
if estab:
    print(f"ACHOU ESTABELECIMENTO: {estab}")
    # situacao_cadastral is at index 5 usually
    print(f"SITUACAO: {estab[5]}")
else:
    print("NÃO ACHOU ESTABELECIMENTO")

conn.close()
