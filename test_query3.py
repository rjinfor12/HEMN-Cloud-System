import sqlite3

def run():
    conn = sqlite3.connect('/var/www/hemn_cloud/cnpj.db')
    cursor = conn.cursor()
    
    print("\n--- NAME QUERY WITH BOUNDS ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM socios WHERE nome_socio >= 'ROGERIO' AND nome_socio < 'ROGERIP' LIMIT 50")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- NAME EMPRESA QUERY WITH BOUNDS ---")
    cursor.execute("EXPLAIN QUERY PLAN SELECT cnpj_basico FROM empresas WHERE razao_social >= 'ROGERIO' AND razao_social < 'ROGERIP' LIMIT 50")
    for row in cursor.fetchall():
        print(row)

if __name__ == '__main__':
    run()
