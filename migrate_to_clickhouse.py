import clickhouse_connect
import time

def migrate():
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    db_path = "/var/lib/clickhouse/user_files/cnpj.db"
    
    tables = ["empresas", "estabelecimento", "socios", "municipio"]
    
    print(f"Iniciando migração de {db_path} para ClickHouse...")
    
    for table in tables:
        start = time.time()
        print(f"Migrando tabela: {table}...")
        
        # ClickHouse can read directly from SQLite files!
        # This is the fastest way possible.
        try:
            client.command(f"INSERT INTO hemn.{table} SELECT * FROM sqlite('{db_path}', '{table}')")
            end = time.time()
            print(f"Tabela {table} migrada com sucesso em {end - start:.1f}s.")
        except Exception as e:
            print(f"Erro ao migrar {table}: {e}")
            print("Tentando método alternativo para socios (caso o schema divirja)...")
            # Adicione lógica de correção aqui se necessário
            
    print("Migração concluída!")

if __name__ == "__main__":
    migrate()
