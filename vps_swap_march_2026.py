import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run_ch(query):
    print(f"Executing: {query}")
    cmd = f'clickhouse-client -q "{query}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err: print(f"STDERR: {err}")
    return res

def perform_swap():
    print("--- INICIANDO SWAP ATÔMICO PARA MARÇO/2026 ---")
    
    # 1. Deduplicate municipio in tmp
    print("Deduplicando tabela 'municipio'...")
    run_ch("CREATE TABLE hemn_update_tmp.municipio_clean AS hemn_update_tmp.municipio")
    run_ch("TRUNCATE TABLE hemn_update_tmp.municipio_clean")
    run_ch("INSERT INTO hemn_update_tmp.municipio_clean SELECT DISTINCT * FROM hemn_update_tmp.municipio")
    run_ch("EXCHANGE TABLES hemn_update_tmp.municipio AND hemn_update_tmp.municipio_clean")
    run_ch("DROP TABLE hemn_update_tmp.municipio_clean")

    # 2. Swap core tables
    core_tables = ["empresas", "estabelecimento", "socios", "municipio"]
    for t in core_tables:
        print(f"Swap {t}...")
        run_ch(f"EXCHANGE TABLES hemn.{t} AND hemn_update_tmp.{t}")

    # 3. Move/Rename new reference tables (those that didn't exist in 'hemn')
    ref_tables = ["cnae", "motivo", "natureza_juridica", "paises", "qualificacao_socio", "simples"]
    for t in ref_tables:
        print(f"Movendo {t} para produção...")
        run_ch(f"DROP TABLE IF EXISTS hemn.{t}")
        run_ch(f"RENAME TABLE hemn_update_tmp.{t} TO hemn.{t}")

    # 4. Update Metadata
    print("Atualizando meta-informações da base...")
    run_ch("TRUNCATE TABLE hemn._metadata")
    run_ch("INSERT INTO hemn._metadata (db_version) VALUES ('Março/2026')")

    # 5. Optimize View (Using the new 'cnpj' column for performance)
    print("Otimizando full_view...")
    view_sql = """
    CREATE OR REPLACE VIEW hemn.full_view AS
    SELECT
        e.cnpj_basico, e.razao_social,
        est.cnpj_ordem, est.cnpj_dv, est.matriz_filial, est.nome_fantasia,
        est.situacao_cadastral, est.data_situacao_cadastral, est.motivo_situacao_cadastral,
        est.uf, est.municipio, est.ddd1, est.telefone1, est.ddd2, est.telefone2,
        est.correio_eletronico, est.logradouro, est.bairro, est.cep,
        est.cnpj AS cnpj_completo
    FROM hemn.empresas AS e
    INNER JOIN hemn.estabelecimento AS est ON e.cnpj_basico = est.cnpj_basico
    """
    run_ch(view_sql)

    print("--- SWAP CONCLUÍDO COM SUCESSO ---")

if __name__ == "__main__":
    perform_swap()
    client.close()
