import sqlite3
import pandas as pd

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def test_optimized():
    conn = sqlite3.connect(DB_PATH)
    
    # Natal, RN code is 1761
    m_code = "1761"
    sit = "02" # Ativa
    
    print(f"Buscando as primeiras 10 empresas ATIVAS em NATAL (Cod {m_code})...")
    
    # Query rápida só no estabelecimento para ver se o código do município bate
    q1 = "SELECT cnpj_basico, cnpj_ordem, cnpj_dv, uf, municipio FROM estabelecimento WHERE municipio = ? AND situacao_cadastral = ? LIMIT 10"
    df1 = pd.read_sql_query(q1, conn, params=[m_code, sit])
    print("Resultados apenas em Estabelecimento:")
    print(df1)
    
    if df1.empty:
        print("AVISO: Nenhum estabelecimento ativo encontrado com o código 1761.")
    else:
        # Tentar o JOIN com apenas um cnpj
        one_cnpj = df1.iloc[0]['cnpj_basico']
        print(f"\nTestando JOIN com empresas para o CNPJ Básico: {one_cnpj}...")
        q2 = "SELECT e.razao_social FROM empresas e WHERE e.cnpj_basico = ?"
        res2 = conn.execute(q2, (one_cnpj,)).fetchone()
        print(f"Razão Social encontrada: {res2}")

    conn.close()

if __name__ == "__main__":
    test_optimized()
