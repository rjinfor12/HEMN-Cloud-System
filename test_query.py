import sqlite3

def run():
    conn = sqlite3.connect('/var/www/hemn_cloud/cnpj.db')
    cursor = conn.cursor()
    
    print("--- CPF OR QUERY ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM socios WHERE cnpj_cpf_socio = '09752279473' OR cnpj_cpf_socio = '***522794**' LIMIT 50")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- CPF IN QUERY ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM socios WHERE cnpj_cpf_socio IN ('09752279473', '***522794**') LIMIT 50")
    for row in cursor.fetchall():
        print(row)

    print("\n--- NAME QUERY ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM socios WHERE nome_socio LIKE 'ROGERIO%' LIMIT 50")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- NAME EMPRESA QUERY ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM empresas WHERE razao_social LIKE 'ROGERIO%' LIMIT 50")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- JOIN QUERY ---")
    query = """
        SELECT e.razao_social, 
               est.cnpj_basico || est.cnpj_ordem || est.cnpj_dv AS cnpj_completo,
               CASE WHEN est.situacao_cadastral = '02' THEN 'ATIVA' ELSE 'BAIXADA/INATIVA' END AS situacao,
               s.nome_socio, s.cnpj_cpf_socio,
               est.correio_eletronico AS email_novo,
               est.logradouro || ', ' || est.numero || ' - ' || est.bairro || ' - ' || COALESCE(m.descricao, 'N/A') || '/' || est.uf AS endereco_completo,
               est.telefone1 AS telefone_novo,
               est.ddd1 AS ddd_novo,
               'FIXO' AS tipo_telefone
        FROM empresas e
        JOIN estabelecimento est ON e.cnpj_basico = est.cnpj_basico
        LEFT JOIN socios s ON e.cnpj_basico = s.cnpj_basico
        LEFT JOIN municipio m ON est.municipio = m.codigo
        WHERE e.cnpj_basico IN ('00000000', '11111111')
        ORDER BY CASE WHEN est.situacao_cadastral = '02' THEN 1 ELSE 2 END
        LIMIT 50
    """
    cursor.execute("EXPLAIN QUERY PLAN " + query)
    for row in cursor.fetchall():
        print(row)

if __name__ == '__main__':
    run()
