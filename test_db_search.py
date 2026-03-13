import sqlite3

db_path = r'C:\HEMN_SYSTEM_DB\cnpj.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Busca por NOME (ROGERIO ELIAS DO NASCIMENTO) ---")
cursor.execute("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM socios WHERE nome_socio LIKE '%ROGERIO ELIAS DO NASCIMENTO%'")
for row in cursor.fetchall():
    print(row)

print("\n--- Busca por CPF (522794) na tabela Socios ---")
cursor.execute("SELECT cnpj_basico, nome_socio, cnpj_cpf_socio FROM socios WHERE cnpj_cpf_socio LIKE '%522794%' AND nome_socio LIKE '%ROGERIO%'")
for row in cursor.fetchall():
    print(row)

print("\n--- Busca por CPF na tabela Empresas (MEI) ---")
cursor.execute("SELECT cnpj_basico, razao_social FROM empresas WHERE razao_social LIKE '%ROGERIO ELIAS%'")
for row in cursor.fetchall():
    print(row)

conn.close()
