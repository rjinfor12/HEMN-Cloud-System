import sqlite3
import pandas as pd

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"
conn = sqlite3.connect(db_path)

cpf = "09752279473"
print(f"--- Buscando CPF: {cpf} em SOCIOS ---")
q1 = "SELECT * FROM socios WHERE cnpj_cpf_socio = ? OR cnpj_cpf_socio LIKE ?"
df1 = pd.read_sql_query(q1, conn, params=[cpf, f"%{cpf[3:9]}%"])
print(df1[['cnpj_basico', 'nome_socio', 'cnpj_cpf_socio']])

print(f"\n--- Buscando CPF: {cpf} em EMPRESAS (MEI) ---")
q2 = "SELECT * FROM empresas WHERE razao_social LIKE ?"
df2 = pd.read_sql_query(q2, conn, params=[f"%{cpf}%"])
print(df2[['cnpj_basico', 'razao_social']])

conn.close()
