import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def check_mei_socio():
    try:
        conn = sqlite3.connect(db_path)
        cnpj_basico_mei = "18528540"
        
        print(f"Buscando sócios para o CNPJ básico {cnpj_basico_mei} (MEI encontrado)...")
        query = f"SELECT * FROM socios WHERE cnpj_basico = '{cnpj_basico_mei}'"
        df = pd.read_sql_query(query, conn)
        print(df)

        print("\nBuscando na tabela empresas para confirmar a razão social...")
        query_e = f"SELECT * FROM empresas WHERE cnpj_basico = '{cnpj_basico_mei}'"
        df_e = pd.read_sql_query(query_e, conn)
        print(df_e)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_mei_socio()
