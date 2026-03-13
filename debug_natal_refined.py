import sqlite3
import pandas as pd

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def test_query():
    conn = sqlite3.connect(DB_PATH)
    
    m = pd.read_sql_query("SELECT * FROM municipio WHERE descricao = 'NATAL'", conn)
    print("Municipios encontrados EXATAMENTE como 'NATAL':")
    print(m)
    
    if m.empty:
        print("NATAL exato não encontrado!")
    else:
        for idx, row in m.iterrows():
            m_code = row['codigo']
            n_count = conn.execute("SELECT count(*) FROM estabelecimento WHERE municipio = ?", (m_code,)).fetchone()[0]
            print(f"Total estabelecimentos em {row['descricao']} (code {m_code}): {n_count}")

    # Checar se existe a tabela empresas_socio ou algo assim (as we join empresas)
    e_count = conn.execute("SELECT count(*) FROM empresas LIMIT 1").fetchone()
    print(f"Empresas table exists and has data: {e_count is not None}")

    conn.close()

if __name__ == "__main__":
    test_query()
