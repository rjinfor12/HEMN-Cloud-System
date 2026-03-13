import sqlite3
import pandas as pd
import unicodedata

db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def debug_search():
    name_input = "ROGÉRIO ELIAS DO NASCIMENTO JUNIOR"
    name_clean = remove_accents(name_input.upper().strip())
    cpf_miolo = "522794"

    try:
        conn = sqlite3.connect(db_path)
        print(f"Conectado ao banco: {db_path}")

        # 1. Testar busca por nome normalizado
        print(f"\nBusca por nome normalizado: {name_clean}")
        q1 = f"SELECT nome_socio, cnpj_cpf_socio FROM socios WHERE nome_socio = '{name_clean}'"
        df1 = pd.read_sql_query(q1, conn)
        print("Resultado em Sócios:")
        print(df1)

        # 2. Testar busca em empresas (MEI)
        print(f"\nBusca por Razão Social (MEI): {name_clean}")
        q2 = f"SELECT razao_social, cnpj_basico FROM empresas WHERE razao_social LIKE '{name_clean}%'"
        df2 = pd.read_sql_query(q2, conn)
        print("Resultado em Empresas:")
        print(df2)

        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    debug_search()
