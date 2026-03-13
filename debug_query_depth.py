import sqlite3
import pandas as pd

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def test_full_query():
    conn = sqlite3.connect(DB_PATH)
    
    # Simular filtros vindos do front
    # Se o usuário apenas selecionou Natal/RN e Situação Ativa (02)
    uf = "RN"
    cidade = "NATAL"
    sit = "02"
    
    # 1. Pegar código do município
    m = pd.read_sql_query("SELECT codigo FROM municipio WHERE descricao LIKE ?", conn, params=[f"%{cidade}%"])
    print(f"Municípios 'NATAL': {m['codigo'].tolist()}")
    m_codes = m['codigo'].tolist()
    
    # 2. Query completa simplificada
    conds = ["estab.situacao_cadastral = ?", "estab.uf = ?"]
    params = [sit, uf]
    
    # Usando o código exato se soubermos (1761) ou a lógica do engine (LIKE no municipio)
    # No cloud_engine.py: conds.append("m.descricao LIKE ?"); params.append(f"%{filters['cidade'].upper()}%")
    
    q = f"""
        SELECT count(*)
        FROM estabelecimento estab 
        JOIN empresas e ON estab.cnpj_basico = e.cnpj_basico 
        LEFT JOIN municipio m ON estab.municipio = m.codigo 
        WHERE estab.situacao_cadastral = ? AND estab.uf = ? AND m.descricao LIKE ?
    """
    p = [sit, uf, f"%{cidade}%"]
    
    count = conn.execute(q, p).fetchone()[0]
    print(f"Resultado da Query (Ativa + RN + LIKE '%NATAL%'): {count}")
    
    # Testar sem o JOIN com empresas (pode ser que o JOIN esteja filtrando)
    q2 = "SELECT count(*) FROM estabelecimento estab LEFT JOIN municipio m ON estab.municipio = m.codigo WHERE estab.situacao_cadastral = ? AND estab.uf = ? AND m.descricao LIKE ?"
    count2 = conn.execute(q2, p).fetchone()[0]
    print(f"Resultado sem JOIN empresas: {count2}")

    conn.close()

if __name__ == "__main__":
    test_full_query()
