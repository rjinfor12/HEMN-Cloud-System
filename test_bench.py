import sqlite3
import time

db_path = r'C:\HEMN_SYSTEM_DB\cnpj.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('PRAGMA case_sensitive_like = ON')

names = [
    'GERALDO APARECIDO LOPES',
    'SANDRA APARECIDA RIBEIRO',
    'LUCAS YAN GUERRA MILANEZ',
    'NATALIA PAULA MENDES',
    'ZAQUEU DE OLIVEIRA ARAUJO',
    'NADSON REIS SANTOS',
    'JOSE RICARDO LUCENTE',
    'LAURA GALVAO BARBOSA DE OLIVEIRA'
]

for name in names:
    print(f"\n--- Testing: {name} ---")
    
    # Prefix Search
    s = time.time()
    c.execute("SELECT cnpj_basico FROM socios WHERE nome_socio LIKE ? LIMIT 100", (name + '%',))
    r1 = c.fetchall()
    t1 = time.time() - s
    print(f"Prefix Search: {t1:.4f}s | count: {len(r1)}")
    
    # Elastic Search
    s = time.time()
    elastic_q = f"%{name.replace(' ', '%')}%"
    c.execute("SELECT cnpj_basico, cnpj_cpf_socio FROM socios WHERE nome_socio LIKE ? LIMIT 20", (elastic_q,))
    r2 = c.fetchall()
    t2 = time.time() - s
    print(f"Elastic Search: {t2:.4f}s | count: {len(r2)}")

conn.close()
