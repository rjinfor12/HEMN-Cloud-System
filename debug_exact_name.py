import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_exact_name_no_cpf():
    try:
        conn = sqlite3.connect(db_path)
        print("Buscando por nome exato 'ROGERIO ELIAS DO NASCIMENTO JUNIOR' em socios (Sem filtro de CPF)...")

        query = """
        SELECT 
            nome_socio, 
            cnpj_cpf_socio, 
            cnpj_basico
        FROM socios 
        WHERE nome_socio = 'ROGERIO ELIAS DO NASCIMENTO JUNIOR'
        """
        
        df = pd.read_sql_query(query, conn)
        print(df)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_exact_name_no_cpf()
