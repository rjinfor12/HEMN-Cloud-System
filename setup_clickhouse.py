import clickhouse_connect

def setup():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    print("Criando Banco de Dados HEMN...")
    client.command('CREATE DATABASE IF NOT EXISTS hemn')
    
    print("Criando Tabela: empresas...")
    client.command('''
        CREATE TABLE IF NOT EXISTS hemn.empresas (
            cnpj_basico String,
            razao_social String,
            natureza_juridica String,
            qualificacao_responsavel String,
            porte_empresa String,
            ente_federativo_responsavel String,
            capital_social Float64
        ) ENGINE = MergeTree()
        ORDER BY (razao_social, cnpj_basico)
    ''')
    
    print("Criando Tabela: estabelecimento...")
    client.command('''
        CREATE TABLE IF NOT EXISTS hemn.estabelecimento (
            cnpj_basico String,
            cnpj_ordem String,
            cnpj_dv String,
            matriz_filial String,
            nome_fantasia String,
            situacao_cadastral String,
            data_situacao_cadastral String,
            motivo_situacao_cadastral String,
            nome_cidade_exterior String,
            pais String,
            data_inicio_atividades String,
            cnae_fiscal String,
            cnae_fiscal_secundaria String,
            tipo_logradouro String,
            logradouro String,
            numero String,
            complemento String,
            bairro String,
            cep String,
            uf String,
            municipio String,
            ddd1 String,
            telefone1 String,
            ddd2 String,
            telefone2 String,
            ddd_fax String,
            fax String,
            correio_eletronico String,
            situacao_especial String,
            data_situacao_especial String,
            cnpj String
        ) ENGINE = MergeTree()
        ORDER BY (cnpj, cnpj_basico, uf, municipio)
    ''')
    
    print("Criando Tabela: socios...")
    client.command('''
        CREATE TABLE IF NOT EXISTS hemn.socios (
            cnpj String,
            cnpj_basico String,
            identificador_de_socio String,
            nome_socio String,
            cnpj_cpf_socio String,
            qualificacao_socio String,
            data_entrada_sociedade String,
            pais String,
            representante_legal String,
            nome_representante String,
            qualificacao_representante_legal String,
            faixa_etaria String
        ) ENGINE = MergeTree()
        ORDER BY (cnpj_cpf_socio, nome_socio, cnpj, cnpj_basico)
    ''')
    
    print("Criando Tabela: municipio...")
    client.command('''
        CREATE TABLE IF NOT EXISTS hemn.municipio (
            codigo String,
            descricao String
        ) ENGINE = MergeTree()
        ORDER BY (codigo)
    ''')
    
    print("Schema ClickHouse configurado com sucesso!")

if __name__ == "__main__":
    setup()
