import clickhouse_connect

client = clickhouse_connect.get_client(
    host='129.121.45.136', 
    username='hemn', 
    password='HeMNSecurePassword2024!', 
    database='hemn', 
    port=8123
)

query = """
SELECT s.nome_socio, s.cnpj_cpf_socio, e.razao_social, e.cnpj_basico
FROM hemn.socios s 
JOIN hemn.empresas e ON s.cnpj_basico = e.cnpj_basico
WHERE s.cnpj_cpf_socio IN ('***522794**')
LIMIT 10
"""
res = client.query(query)
for row in res.result_rows:
    print(row)
