import clickhouse_connect
import time

def test_optimized_query():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # Generate 50,000 dummy CNPJs for testing
    print("Generating test data...")
    test_cnpjs = [str(x).zfill(8) for x in range(1, 50001)]
    
    start_time = time.time()
    print("Testing standard IN clause...")
    
    q_in = f"""
    SELECT 
        estab.cnpj_basico AS cpf_mask,
        estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, 
        estab.situacao_cadastral, estab.uf, mun.descricao AS municipio_nome, 
        estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, 
        estab.correio_eletronico, estab.tipo_logradouro, estab.logradouro, 
        estab.numero, estab.complemento, estab.bairro, estab.cep, 
        estab.cnae_fiscal, estab.municipio
    FROM hemn.estabelecimento estab
    LEFT JOIN hemn.municipio mun ON estab.municipio = mun.codigo
    WHERE estab.cnpj_basico IN %(keys)s
    """
    res_in = client.query(q_in, {'keys': test_cnpjs})
    t_in = time.time() - start_time
    print(f"IN clause took: {t_in:.2f}s, Rows: {len(res_in.result_rows)}")

if __name__ == "__main__":
    test_optimized_query()
