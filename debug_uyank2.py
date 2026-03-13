import sqlite3
import pandas as pd
from consolidation_engine import ConsolidationEngine

engine = ConsolidationEngine("", "")
conn = sqlite3.connect(r'C:\HEMN_SYSTEM_DB\cnpj.db')

query = """
SELECT 
    s.cnpj_basico, 
    e.razao_social, 
    s.nome_socio, 
    s.cnpj_cpf_socio,
    estab.situacao_cadastral,
    m.descricao
FROM socios s
LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
WHERE (s.nome_socio LIKE '%UYANK DOUGLAS SIQUEIRA DE LIMA%' OR s.nome_representante LIKE '%UYANK DOUGLAS SIQUEIRA DE LIMA%') 
AND (s.cnpj_cpf_socio LIKE '%173384%' OR s.cnpj_cpf_socio = '08173384460')
"""
print("Running DB Query...")
df = pd.read_sql_query(query, conn)
print("DF Result:\n", df.to_dict())

print("\nRunning Engine Direct Search...")
res = engine.search_cnpj_by_name_cpf(r'C:\HEMN_SYSTEM_DB\cnpj.db', 'uyank douglas siqueira de lima', '08173384460')
print("Engine Result:\n", res)

conn.close()
