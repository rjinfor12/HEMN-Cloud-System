import pandas as pd
import time
import sqlite3

from consolidation_engine import ConsolidationEngine
engine = ConsolidationEngine('a', 'b')

# Get some data
db_path = r'C:/Users/Junior T.I/OneDrive/Área de Trabalho/cruzar/cnpj.db'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
query = "SELECT * FROM estabelecimento WHERE uf = 'SP' AND situacao_cadastral = '02' LIMIT 50000"
chunk = pd.read_sql_query(query, conn)
print(f"Loaded {len(chunk)} rows")

t0 = time.time()
tipo_req = "CELULAR"

# Address vectorization
chunk['tipo_log_str'] = chunk['tipo_logradouro'].fillna('').astype(str).str.strip().replace('None', '')
chunk['log_str'] = chunk['logradouro'].fillna('').astype(str).str.strip().replace('None', '')
chunk['LOGRADOURO'] = (chunk['tipo_log_str'] + ' ' + chunk['log_str']).str.strip()

chunk['NUMERO'] = chunk['numero'].fillna('').astype(str).str.strip().replace('None', '')
chunk['COMPLEMENTO'] = chunk['complemento'].fillna('').astype(str).str.strip().replace('None', '')
chunk['BAIRRO'] = chunk['bairro'].fillna('').astype(str).str.strip().replace('None', '')

# For testing municipio
if 'municipio_nome' not in chunk.columns:
    chunk['municipio_nome'] = ''

mun_nome = chunk['municipio_nome'].fillna('').astype(str).str.strip().replace('None', '')
mun_cod = chunk['municipio'].fillna('').astype(str).str.strip().replace('None', '')
chunk['CIDADE'] = mun_nome.where(mun_nome != '', mun_cod)

chunk['UF_END'] = chunk['uf'].fillna('').astype(str).str.strip().replace('None', '')
chunk['CEP'] = chunk['cep'].fillna('').astype(str).str.strip().replace('None', '')

chunk.drop(columns=['tipo_log_str', 'log_str'], inplace=True, errors='ignore')

# Contact Vectorization
def extract_digits(s):
    return s.fillna('').astype(str).str.replace(r'\D', '', regex=True)

d1 = extract_digits(chunk['ddd1'])
t1 = extract_digits(chunk['telefone1'])
d2 = extract_digits(chunk['ddd2'])
t2 = extract_digits(chunk['telefone2'])

v1_valid = t1.str.len() == 8
v1_first = t1.str[:1]
t1_is_cel = v1_valid & v1_first.isin(['1', '5', '6', '7', '8', '9'])
t1_is_fix = v1_valid & v1_first.isin(['2', '3', '4'])

tipo1 = pd.Series("", index=chunk.index)
tipo1.loc[t1_is_cel] = "CELULAR"
tipo1.loc[t1_is_fix] = "FIXO"

t1_fmt = pd.Series("", index=chunk.index)
t1_fmt.loc[t1_is_cel] = "9" + t1.loc[t1_is_cel]
t1_fmt.loc[t1_is_fix] = t1.loc[t1_is_fix]

v2_valid = t2.str.len() == 8
v2_first = t2.str[:1]
t2_is_cel = v2_valid & v2_first.isin(['1', '5', '6', '7', '8', '9'])
t2_is_fix = v2_valid & v2_first.isin(['2', '3', '4'])

tipo2 = pd.Series("", index=chunk.index)
tipo2.loc[t2_is_cel] = "CELULAR"
tipo2.loc[t2_is_fix] = "FIXO"

t2_fmt = pd.Series("", index=chunk.index)
t2_fmt.loc[t2_is_cel] = "9" + t2.loc[t2_is_cel]
t2_fmt.loc[t2_is_fix] = t2.loc[t2_is_fix]

best_ddd = pd.Series("", index=chunk.index)
best_tel = pd.Series("", index=chunk.index)
best_tipo = pd.Series("", index=chunk.index)

if tipo_req in ["CELULAR", "FIXO"]:
    match_t1 = (tipo1 == tipo_req)
    match_t2 = (tipo2 == tipo_req)
    
    best_ddd.loc[match_t1] = d1.loc[match_t1]
    best_tel.loc[match_t1] = t1_fmt.loc[match_t1]
    best_tipo.loc[match_t1] = tipo1.loc[match_t1]
    
    fill_t2 = match_t2 & ~match_t1
    best_ddd.loc[fill_t2] = d2.loc[fill_t2]
    best_tel.loc[fill_t2] = t2_fmt.loc[fill_t2]
    best_tipo.loc[fill_t2] = tipo2.loc[fill_t2]
    
    rem = (best_tel == "")
    fill_f1 = rem & (t1_fmt != "")
    best_ddd.loc[fill_f1] = d1.loc[fill_f1]
    best_tel.loc[fill_f1] = t1_fmt.loc[fill_f1]
    best_tipo.loc[fill_f1] = tipo1.loc[fill_f1]
    
    rem2 = rem & ~fill_f1
    fill_f2 = rem2 & (t2_fmt != "")
    best_ddd.loc[fill_f2] = d2.loc[fill_f2]
    best_tel.loc[fill_f2] = t2_fmt.loc[fill_f2]
    best_tipo.loc[fill_f2] = tipo2.loc[fill_f2]
else:
    has_t1 = (t1_fmt != "")
    has_t2 = (t2_fmt != "")
    
    best_ddd.loc[has_t1] = d1.loc[has_t1]
    best_tel.loc[has_t1] = t1_fmt.loc[has_t1]
    best_tipo.loc[has_t1] = tipo1.loc[has_t1]
    
    fill_f2 = has_t2 & ~has_t1
    best_ddd.loc[fill_f2] = d2.loc[fill_f2]
    best_tel.loc[fill_f2] = t2_fmt.loc[fill_f2]
    best_tipo.loc[fill_f2] = tipo2.loc[fill_f2]

chunk['DDD_P'] = best_ddd
chunk['TEL_P'] = best_tel
chunk['TIPO_P'] = best_tipo

email = chunk['correio_eletronico'].fillna('').astype(str).str.strip().str.lower()
chunk['EMAIL_P'] = email.where(email != 'none', '')

t1 = time.time()
print(f"Vectorized Apply: {t1 - t0:.2f}s")
