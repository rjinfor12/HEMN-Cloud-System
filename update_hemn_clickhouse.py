import clickhouse_connect
import time
import sys

# DATABASE_NAME = 'hemn'
# TMP_DATABASE = 'hemn_update_tmp'

def run_update(host='localhost', port=8123, username='default', password='', db_path='/var/lib/clickhouse/user_files/cnpj.db'):
    client = clickhouse_connect.get_client(host=host, port=port, username=username, password=password)
    
    tables = ["empresas", "estabelecimento", "socios", "municipio"]
    
    print(f"--- INICIANDO ATUALIZAÇÃO DA BASE MATRIZ (RECEITA) ---")
    print(f"Fonte: {db_path}")

    # 1. Create temporary database for isolation
    client.command("CREATE DATABASE IF NOT EXISTS hemn_update_tmp")
    
    for table in tables:
        start = time.time()
        print(f"Processando tabela: {table}...")
        
        # 1.1 Draft new table in tmp (matching schema)
        client.command(f"DROP TABLE IF EXISTS hemn_update_tmp.{table}")
        client.command(f"CREATE TABLE hemn_update_tmp.{table} AS hemn.{table}")
        client.command(f"TRUNCATE TABLE hemn_update_tmp.{table}")
        
        # 1.2 Load from SQLite
        print(f"Copiando dados do SQLite para hemn_update_tmp.{table}...")
        try:
            if table == 'estabelecimento':
                # Format specific columns for 'estabelecimento' to avoid common padding issues (situacao, cnae, municipio)
                # We select explicitly 31 columns matching ClickHouse schema
                query = f"""
                    INSERT INTO hemn_update_tmp.{table} (
                        cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia, 
                        situacao_cadastral, data_situacao_cadastral, motivo_situacao_cadastral, 
                        nome_cidade_exterior, pais, data_inicio_atividades, cnae_fiscal, 
                        cnae_fiscal_secundaria, tipo_logradouro, logradouro, numero, 
                        complemento, bairro, cep, uf, municipio, ddd1, telefone1, 
                        ddd2, telefone2, ddd_fax, fax, correio_eletronico, 
                        situacao_especial, data_situacao_especial, cnpj
                    )
                    SELECT 
                        cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia,
                        lpad(toString(situacao_cadastral), 2, '0'),
                        data_situacao_cadastral, motivo_situacao_cadastral, nome_cidade_exterior, pais,
                        data_inicio_atividades,
                        lpad(toString(cnae_fiscal), 7, '0'),
                        cnae_fiscal_secundaria, tipo_logradouro, logradouro, numero, complemento,
                        bairro, cep, uf, 
                        lpad(toString(municipio), 4, '0'),
                        ddd1, telefone1, ddd2, telefone2, ddd_fax, fax,
                        correio_eletronico, situacao_especial, data_situacao_especial, cnpj
                    FROM sqlite('{db_path}', '{table}')
                    SETTINGS max_insert_threads = 8, max_memory_usage = 4000000000
                """
                client.command(query)
            elif table == 'socios':
                # SQLite 'socios' has 12 columns, ClickHouse has 13 (missing 'socio_chave')
                query = f"""
                    INSERT INTO hemn_update_tmp.{table}
                    SELECT 
                        cnpj, cnpj_basico, identificador_de_socio, nome_socio, 
                        cnpj_cpf_socio, qualificacao_socio, data_entrada_sociedade, 
                        pais, representante_legal, nome_representante, 
                        qualificacao_representante_legal, faixa_etaria,
                        '' as socio_chave
                    FROM sqlite('{db_path}', '{table}')
                    SETTINGS max_insert_threads = 8, max_memory_usage = 4000000000
                """
                client.command(query)
            else:
                client.command(f"INSERT INTO hemn_update_tmp.{table} SELECT * FROM sqlite('{db_path}', '{table}')")
            
            load_time = time.time() - start
            # Fix count query to use query() instead of command() for results
            count_res = client.query(f"SELECT count() FROM hemn_update_tmp.{table}")
            count = count_res.result_rows[0][0]
            print(f"Copiado {count} registros em {load_time:.1f}s.")
            
            # 1.3 Atomic Swap (Exchange Tables)
            print(f"Realizando troca atômica (EXCHANGE) com a base principal...")
            client.command(f"EXCHANGE TABLES hemn.{table} AND hemn_update_tmp.{table}")
            print(f"Tabela {table} atualizada com sucesso.")
            
        except Exception as e:
            print(f"ERRO CRÍTICO NA TABELA {table}: {e}")
            import traceback
            traceback.print_exc()
            print("Abortando atualização para esta tabela.")

    # 2. Cleanup
    print("Finalizando e limpando base temporária...")
    # Optional: Keep tmp for a while if space allows, but here we drop
    # client.command("DROP DATABASE hemn_update_tmp")
    
    print("--- ATUALIZAÇÃO CONCLUÍDA ---")

if __name__ == "__main__":
    # In production, these would be args or env vars
    run_update()
