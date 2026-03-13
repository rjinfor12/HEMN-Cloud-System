import sqlite3

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def check_types():
    conn = sqlite3.connect(DB_PATH)
    
    print("Checking types for Natal:")
    m_info = conn.execute("SELECT typeof(codigo), codigo FROM municipio WHERE descricao = 'NATAL'").fetchone()
    print(f"municipio.codigo: {m_info}")
    
    e_info = conn.execute("SELECT typeof(municipio), municipio FROM estabelecimento WHERE municipio LIKE '%1761%' LIMIT 1").fetchone()
    print(f"estabelecimento.municipio: {e_info}")

    # Test comparison
    if m_info and e_info:
        c1 = m_info[1]
        c2 = e_info[1]
        print(f"Direct comparison ('{c1}' == {c2}): {c1 == c2}")
        
    conn.close()

if __name__ == "__main__":
    check_types()
