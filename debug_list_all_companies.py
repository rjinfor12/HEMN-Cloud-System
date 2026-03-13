import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def debug_list_all_rogerio_elias_companies():
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT razao_social, cnpj_basico FROM empresas WHERE razao_social LIKE 'ROGERIO ELIAS%'"
        df = pd.read_sql_query(query, conn)
        
        # Mostrar tudo sem truncar
        pd.set_option('display.max_rows', None)
        print(df)
        
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_list_all_rogerio_elias_companies()
