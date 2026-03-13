import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def check_other_meis():
    try:
        conn = sqlite3.connect(db_path)
        cnpjs = ["23573445", "38262186"]
        
        for cnpj in cnpjs:
            print(f"\n--- Detalhes do CNPJ {cnpj} ---")
            q_emp = f"SELECT * FROM empresas WHERE cnpj_basico = '{cnpj}'"
            print(pd.read_sql_query(q_emp, conn))
            
            q_est = f"SELECT * FROM estabelecimento WHERE cnpj_basico = '{cnpj}'"
            print(pd.read_sql_query(q_est, conn))

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_other_meis()
