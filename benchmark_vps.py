import clickhouse_connect
import time

def benchmark():
    host = '86.48.17.194'
    user = 'root'
    pw = '^QP67kXax9AyuvF%'
    
    client = clickhouse_connect.get_client(host=host, port=8123, username=user, password=pw)
    
    # Test Recife, PE (Restrictive filter)
    uf = 'PE'
    m_code = '2531' # Recife code (from earlier logs)
    
    print(f"--- BENCHMARK: PE | RECIFE ---")
    
    # Standard Join (The one that was slow)
    q_standard = f"""
    SELECT count()
    FROM hemn.estabelecimento estab
    INNER JOIN hemn.empresas e ON e.cnpj_basico = estab.cnpj_basico
    WHERE estab.uf = '{uf}' AND estab.municipio = '{m_code}'
    """
    
    start = time.time()
    res1 = client.query(q_standard)
    t1 = time.time() - start
    print(f"Standard Join: {t1:.2f}s, Processed: {res1.result_rows[0][0]}")
    
    # Optimized Subquery Join
    q_optimized = f"""
    SELECT count()
    FROM (
        SELECT cnpj_basico FROM hemn.estabelecimento
        WHERE uf = '{uf}' AND municipio = '{m_code}'
    ) AS estab
    INNER JOIN (
        SELECT cnpj_basico FROM hemn.empresas
    ) AS e ON e.cnpj_basico = estab.cnpj_basico
    SETTINGS join_algorithm = 'hash', max_threads = 8
    """
    
    start = time.time()
    res2 = client.query(q_optimized)
    t2 = time.time() - start
    print(f"Optimized Subquery: {t2:.2f}s, Processed: {res2.result_rows[0][0]}")
    
    # Comparison
    improvement = (t1 / t2) if t2 > 0 else 0
    print(f"\nIMPROVEMENT: {improvement:.1f}x faster")
    
    client.close()

if __name__ == "__main__":
    benchmark()
