import clickhouse_connect

def test_columns():
    try:
        client = clickhouse_connect.get_client(host='129.121.45.136', port=8123, username='default', password='')
        print("Connected to ClickHouse VPS!")
        
        q = """
        SELECT e.razao_social as NOME_DA_EMPRESA, 
               concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
               estab.situacao_cadastral as SITUACAO_CADASTRAL,
               estab.cnae_fiscal as CNAE, 
               estab.logradouro as LOGRADOURO,
               estab.numero as NUMERO_DA_FAIXADA,
               estab.bairro as BAIRRO,
               estab.CIDADE, estab.uf as UF, estab.cep as CEP
        FROM (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            LIMIT 5
        ) as estab 
        JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
        """
        
        res = client.query(q)
        print("Columns:", res.column_names)
        for row in res.result_rows:
            print(row)
            
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test_columns()
