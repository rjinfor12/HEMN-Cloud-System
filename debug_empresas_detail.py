import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_empresas_detail():
    try:
        conn = sqlite3.connect(db_path)
        print("Buscando por '%ROGERIO%NASCIMENTO%' na tabela de empresas...")

        query = """
        SELECT 
            razao_social, 
            cnpj_basico
        FROM empresas 
        WHERE razao_social LIKE '%ROGERIO%'
          AND razao_social LIKE '%NASCIMENTO%'
        """
        
        df = pd.read_sql_query(query, conn)
        print(df)
        
        print("\nFiltrando pelo CPF do usuário (09752279473) na Razão Social...")
        df_cpf = df[df['razao_social'].str.contains('09752279473', na=False)]
        print(df_cpf)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_empresas_detail()
