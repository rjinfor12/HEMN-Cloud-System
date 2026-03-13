import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_junior():
    try:
        conn = sqlite3.connect(db_path)
        print("Buscando por qualquer sócio que tenha 'NASCIMENTO' e 'JUNIOR' no nome...")

        query = """
        SELECT 
            nome_socio, 
            cnpj_cpf_socio, 
            cnpj_basico
        FROM socios 
        WHERE nome_socio LIKE '%NASCIMENTO%' 
          AND nome_socio LIKE '%JUNIOR%'
        LIMIT 20
        """
        
        df = pd.read_sql_query(query, conn)
        print(df)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_junior()
