import sqlite3

def run():
    print("Connecting to DB...")
    conn = sqlite3.connect('/var/www/hemn_cloud/cnpj.db')
    cursor = conn.cursor()
    
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
        LEFT JOIN socios s ON (est.cnpj_basico || est.cnpj_ordem || est.cnpj_dv) = s.cnpj
        LEFT JOIN municipio m ON est.municipio = m.codigo
        WHERE e.cnpj_basico IN ('09752279', '27865757', '00000000')
        ORDER BY CASE WHEN est.situacao_cadastral = '02' THEN 1 ELSE 2 END
        LIMIT 50
    """
    try:
        print("Executing query...")
        cursor.execute(query)
        data = cursor.fetchall()
        print(f"Success! Retrieved {len(data)} rows.")
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == '__main__':
    run()
