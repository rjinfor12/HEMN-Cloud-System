import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def check_socio_23573445():
    try:
        conn = sqlite3.connect(db_path)
        cnpj = "23573445"
        print(f"Buscando sócio para CNPJ {cnpj}...")
        q = f"SELECT * FROM socios WHERE cnpj_basico = '{cnpj}'"
        print(pd.read_sql_query(q, conn))
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_socio_23573445()
