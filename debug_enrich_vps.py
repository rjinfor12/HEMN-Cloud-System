import clickhouse_connect
import pandas as pd

client = clickhouse_connect.get_client(host='127.0.0.1', port=8123)

name = "GILBERTO ALVES DE SOUZA" # From our previous test

q = """
    SELECT 
        s.lookup_key AS lookup_key,
        e.razao_social AS razao_social, 
        estab.cnpj_basico AS cnpj_basico, 
        estab.cnpj_ordem AS cnpj_ordem, 
        estab.cnpj_dv AS cnpj_dv, 
        estab.situacao_cadastral AS situacao_cadastral, 
        estab.uf AS uf, 
        mun.descricao AS municipio_nome, 
        estab.logradouro AS logradouro, 
        estab.numero AS numero, 
        estab.bairro AS bairro, 
        estab.cep AS cep,
        s.nome_socio AS nome_socio
    FROM (
        SELECT cnpj_basico, nome_socio AS lookup_key, nome_socio
        FROM hemn.socios 
        WHERE nome_socio LIKE %(name)s
    ) AS s
    INNER JOIN hemn.estabelecimento AS estab ON s.cnpj_basico = estab.cnpj_basico
    INNER JOIN hemn.empresas AS e ON s.cnpj_basico = e.cnpj_basico
    LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
    LIMIT 5
"""

print(f"Searching for Sócio: {name}...")
res = client.query(q, {'name': f"%{name}%"})
df = pd.DataFrame(res.result_rows, columns=res.column_names)

print("\n--- ENRICHMENT RESULTS ---")
print(df.to_string())
