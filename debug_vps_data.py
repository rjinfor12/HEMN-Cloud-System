import clickhouse_connect
import pandas as pd

client = clickhouse_connect.get_client(host='127.0.0.1', port=8123)

q = """
    SELECT 
        e.razao_social AS NOME, 
        CONCAT(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) AS CNPJ, 
        estab.situacao_cadastral AS SITUACAO,
        estab.cnae_fiscal AS CNAE, 
        estab.logradouro AS RUA,
        estab.numero AS NUMERO,
        estab.bairro AS BAIRRO,
        m.descricao AS CIDADE, 
        estab.uf AS UF, 
        estab.cep AS CEP
    FROM hemn.empresas e
    INNER JOIN hemn.estabelecimento estab ON e.cnpj_basico = estab.cnpj_basico
    LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo
    WHERE estab.uf = 'SP' AND estab.situacao_cadastral = '02'
    LIMIT 10
"""

print("Running Diagnostic Query...")
res = client.query(q)
df = pd.DataFrame(res.result_rows, columns=res.column_names)

print("\n--- RESULTS SAMPLE ---")
print(df.head(10).to_string())

print("\n--- NULL COUNT ---")
print(df.isnull().sum())

print("\n--- EMPTY STRING COUNT ---")
print((df == '').sum())
