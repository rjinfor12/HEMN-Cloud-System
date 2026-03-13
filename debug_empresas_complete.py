import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_empresas_complete_search():
    try:
        conn = sqlite3.connect(db_path)
        print("Buscando por 'ROGERIO%ELIAS%NASCIMENTO%' na tabela de empresas...")

        query = """
        SELECT 
            razao_social, 
            cnpj_basico
        FROM empresas 
        WHERE razao_social LIKE '%ROGERIO%'
          AND razao_social LIKE '%ELIAS%'
          AND razao_social LIKE '%NASCIMENTO%'
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"Resultados encontrados: {len(df)}")
        print(df)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_empresas_complete_search()
