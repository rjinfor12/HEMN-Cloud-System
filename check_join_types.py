import sqlite3

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def check_schema():
    conn = sqlite3.connect(DB_PATH)
    
    print("Schema de 'estabelecimento':")
    res = conn.execute("PRAGMA table_info(estabelecimento)").fetchall()
    for col in res:
        if col[1] in ['municipio', 'uf', 'situacao_cadastral', 'cnpj_basico']:
            print(col)
            
    print("\nSchema de 'municipio':")
    res = conn.execute("PRAGMA table_info(municipio)").fetchall()
    for col in res:
        print(col)

    # Testar o JOIN explicitamente com detecção de falha
    print("\nTestando JOIN explícito para Natal (1761):")
    q = "SELECT count(*) FROM estabelecimento estab JOIN municipio m ON estab.municipio = m.codigo WHERE estab.municipio = '1761'"
    print(f"Count com JOIN: {conn.execute(q).fetchone()[0]}")
    
    q_cast = "SELECT count(*) FROM estabelecimento estab JOIN municipio m ON CAST(estab.municipio AS TEXT) = CAST(m.codigo AS TEXT) WHERE estab.municipio = '1761'"
    print(f"Count com JOIN + CAST: {conn.execute(q_cast).fetchone()[0]}")

    conn.close()

if __name__ == "__main__":
    check_schema()
