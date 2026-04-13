
import sqlite3
import os

db_path = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_carrier.db'

def optimize_db():
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Criando índice na coluna 'telefone'...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portabilidade_telefone ON portabilidade(telefone);")
        
        print("Executando ANALYZE...")
        cursor.execute("ANALYZE;")
        
        print("Verificando novo plano de consulta...")
        cursor.execute("EXPLAIN QUERY PLAN SELECT operadora_id FROM portabilidade WHERE telefone = '11999999999'")
        for row in cursor.fetchall():
            print(row)
            
        conn.commit()
        conn.close()
        print("Otimização concluída com sucesso.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    optimize_db()
