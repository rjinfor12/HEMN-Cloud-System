import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_all_rogerios():
    try:
        conn = sqlite3.connect(db_path)
        print("Listando todos os 'ROGERIO ELIAS' na tabela de sócios...")

        query = """
        SELECT 
            nome_socio, 
            cnpj_cpf_socio, 
            cnpj_basico
        FROM socios 
        WHERE nome_socio LIKE 'ROGERIO ELIAS%'
        """
        
        df = pd.read_sql_query(query, conn)
        print(df)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_all_rogerios()
