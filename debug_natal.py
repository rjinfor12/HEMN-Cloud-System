import sqlite3
import pandas as pd

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def test_query():
    conn = sqlite3.connect(DB_PATH)
    
    # Test 1: Check if Natal exists in municipio table
    m = pd.read_sql_query("SELECT * FROM municipio WHERE descricao LIKE '%NATAL%'", conn)
    print("Municipios encontrados:")
    print(m)
    
    if m.empty:
        print("NATAL não encontrado na tabela municipio!")
        return

    m_code = m.iloc[0]['codigo']
    
    # Test 2: Check establishments in RN
    e_count = conn.execute("SELECT count(*) FROM estabelecimento WHERE uf = 'RN'").fetchone()[0]
    print(f"Total estabelecimentos no RN: {e_count}")

    # Test 3: Check establishments in Natal (using code)
    n_count = conn.execute("SELECT count(*) FROM estabelecimento WHERE municipio = ?", (m_code,)).fetchone()[0]
    print(f"Total estabelecimentos em NATAL (code {m_code}): {n_count}")

    conn.close()

if __name__ == "__main__":
    test_query()
