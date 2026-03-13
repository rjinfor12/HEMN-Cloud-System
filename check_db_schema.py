import sqlite3

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"

def check_schema():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("--- Tabelas na base de dados ---")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(table[0])
            
        # Verificar schema da tabela 'socios' se existir
        if ('socios',) in tables:
            print("\n--- Schema da tabela 'socios' ---")
            cursor.execute("PRAGMA table_info(socios);")
            for col in cursor.fetchall():
                print(col)
                
        conn.close()
    except Exception as e:
        print(f"Erro ao acessar a base: {e}")

if __name__ == "__main__":
    check_schema()
