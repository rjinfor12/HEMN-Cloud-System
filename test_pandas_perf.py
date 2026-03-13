import pandas as pd
import time
import sqlite3

from consolidation_engine import ConsolidationEngine
engine = ConsolidationEngine('a', 'b')

# Get some data
db_path = r'C:/Users/Junior T.I/OneDrive/Área de Trabalho/cruzar/cnpj.db'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
query = "SELECT * FROM estabelecimento WHERE uf = 'SP' AND situacao_cadastral = '02' LIMIT 50000"
df = pd.read_sql_query(query, conn)
print(f"Loaded {len(df)} rows")

t0 = time.time()
r_addr = df.apply(engine._parse_address_columns, axis=1, result_type='expand')
t1 = time.time()
print(f"Address Apply: {t1 - t0:.2f}s")
r_contact = df.apply(lambda r: engine._parse_contact_columns(r, 'CELULAR'), axis=1, result_type='expand')
t2 = time.time()
print(f"Contact Apply: {t2 - t1:.2f}s")
