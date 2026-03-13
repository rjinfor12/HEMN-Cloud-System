import sqlite3
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
cursor = conn.cursor()

nome = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
print(f"Buscando sócio por nome: {nome}")
cursor.execute("SELECT cnpj_basico, cnpj_cpf_socio, nome_socio FROM socios WHERE nome_socio = ?", [nome])
print(cursor.fetchall())

nome_sem_junior = "ROGERIO ELIAS DO NASCIMENTO"
print(f"\nBuscando sócio por nome sem junior: {nome_sem_junior}")
cursor.execute("SELECT cnpj_basico, cnpj_cpf_socio, nome_socio FROM socios WHERE nome_socio = ?", [nome_sem_junior])
print(cursor.fetchall())

conn.close()
