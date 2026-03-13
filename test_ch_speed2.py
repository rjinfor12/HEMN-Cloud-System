import clickhouse_connect
import time

def test_optimized_query():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Generate 50,000 dummy CNPJs for testing
    print("Generating test data...")
    test_cnpjs = [str(x).zfill(8) for x in range(1, 50001)]
    
    start_time = time.time()
    print("Testing Temp Table JOIN strategy...")
    
    # 1. Create a temporary table
    client.command("CREATE TEMPORARY TABLE IF NOT EXISTS temp_keys (cnpj_basico String)")
    
    # 2. Insert keys in one fast block
    client.insert('temp_keys', [[k] for k in test_cnpjs], column_names=['cnpj_basico'])
    t_insert = time.time() - start_time
    print(f"Insertion took: {t_insert:.2f}s")
    
    # 3. Perform the JOIN
    q_join = f"""
    SELECT 
        estab.cnpj_basico AS cpf_mask,
        estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, 
        estab.situacao_cadastral, estab.uf, mun.descricao AS municipio_nome, 
        estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, 
        estab.correio_eletronico, estab.tipo_logradouro, estab.logradouro, 
        estab.numero, estab.complemento, estab.bairro, estab.cep, 
        estab.cnae_fiscal, estab.municipio
    FROM temp_keys tk
    JOIN hemn.estabelecimento estab ON tk.cnpj_basico = estab.cnpj_basico
    LEFT JOIN hemn.municipio mun ON estab.municipio = mun.codigo
    """
    
    start_join = time.time()
    res_join = client.query(q_join)
    t_join = time.time() - start_join
    
    print(f"JOIN extraction took: {t_join:.2f}s, Rows: {len(res_join.result_rows)}")
    print(f"Total time (JOIN strategy): {(time.time() - start_time):.2f}s")

if __name__ == "__main__":
    test_optimized_query()
