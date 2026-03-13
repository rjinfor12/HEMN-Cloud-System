import sqlite3
import pandas as pd

conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')
name = 'UYANK DOUGLAS SIQUEIRA DE LIMA'
cpf_digits = '08173384460'
cpf_miolo = '173384'
cpf_filter_socios = f"AND (s.cnpj_cpf_socio LIKE '%{cpf_miolo}%' OR s.cnpj_cpf_socio = '{cpf_digits}')"

query = f"""
SELECT 
    s.cnpj_basico, 
    e.razao_social, 
    s.nome_socio, 
    s.cnpj_cpf_socio,
    estab.situacao_cadastral
FROM socios s
LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
WHERE (s.nome_socio LIKE '%{name}%') {cpf_filter_socios}
"""
df = pd.read_sql_query(query, conn)
print(df)
conn.close()
