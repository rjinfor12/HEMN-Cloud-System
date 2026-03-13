import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

cnpjs = ['57863854', '08265765', '51763851']
for c in cnpjs:
    print(f"Buscando sócios para CNPJ Básico: {c}")
    cursor.execute("SELECT cnpj_cpf_socio, nome_socio FROM socios WHERE cnpj_basico = ?", [c])
    print(cursor.fetchall())

conn.close()
