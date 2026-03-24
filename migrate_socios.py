import clickhouse_connect
import sys

def migrate():
    print("Iniciando migração da tabela hemn.socios...")
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        
        # 1. Adicionar coluna socio_chave
        print("Adicionando coluna socio_chave...")
        try:
            client.command("ALTER TABLE hemn.socios ADD COLUMN socio_chave String")
        except Exception as e:
            if "already exists" in str(e):
                print("Coluna socio_chave já existe.")
            else:
                raise e
        
        # 2. Popular coluna socio_chave
        # Padrão: NOME + *** + digitos 4-9 do CPF + **
        # substring em ClickHouse é 1-indexed. CPF total 11 digitos. Digitos 4-9 são posições 4,5,6,7,8,9.
        print("Populando coluna socio_chave (Não MEI)...")
        # Nota: natureza_juridica != '2135' (Não MEI) na tabela empresas, mas aqui estamos na socios.
        # Precisamos fazer um join ou carregar baseada no cnpj_basico.
        # Mas o usuário quer todos os sócios preparados.
        # Filtramos apenas CPFs validos (11 digitos) ou já mascarados (***...)
        
        update_query = """
        ALTER TABLE hemn.socios UPDATE socio_chave = concat(upper(nome_socio), ' ***', substring(cnpj_cpf_socio, 4, 6), '**')
        WHERE length(cnpj_cpf_socio) >= 11 OR startsWith(cnpj_cpf_socio, '***')
        """
        client.command(update_query)
        print("Comando de UPDATE enviado com sucesso (processamento em background no ClickHouse).")
        
        client.close()
        print("Migração finalizada.")
    except Exception as e:
        print(f"ERRO NA MIGRAÇÃO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
