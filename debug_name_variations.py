import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_name_variations():
    try:
        conn = sqlite3.connect(db_path)
        print("Buscando por variações do nome 'ROGERIO' e 'NASCIMENTO' e 'ELIAS'...")

        query = """
        SELECT 
            nome_socio, 
            cnpj_cpf_socio, 
            cnpj_basico
        FROM socios 
        WHERE nome_socio LIKE '%ROGERIO%' 
          AND nome_socio LIKE '%NASCIMENTO%'
          AND nome_socio LIKE '%ELIAS%'
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"\nResultados encontrados: {len(df)}")
        print(df)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_name_variations()
