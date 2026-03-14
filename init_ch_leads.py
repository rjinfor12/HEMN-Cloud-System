import clickhouse_connect

def init_db():
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        
        # Criar tabela de leads
        client.command("""
        CREATE TABLE IF NOT EXISTS leads (
            cpf String,
            nome String,
            dt_nascimento String,
            tel_fixo1 String,
            celular1 String,
            uf String,
            regiao String
        ) ENGINE = ReplacingMergeTree()
        ORDER BY (cpf, nome)
        """)
        
        print("Tabela 'leads' criada ou já existente no ClickHouse.")
        client.close()
    except Exception as e:
        print(f"Erro ao conectar ou criar tabela no ClickHouse: {e}")

if __name__ == "__main__":
    init_db()
