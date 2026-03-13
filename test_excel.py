import pandas as pd
import xlsxwriter

df = pd.DataFrame([
    {
        'NOME_DA_EMPRESA': 'BANCO DO BRASIL SA',
        'CNPJ': '00000000008508',
        'SITUACAO_CADASTRAL': '02',
        'CNAE': '6422100',
        'LOGRADOURO': 'CORONEL JOSE SABOIA',
        'NUMERO_DA_FAIXADA': '473',
        'BAIRRO': 'CENTRO',
        'CIDADE': 'SOBRAL',
        'UF': 'CE',
        'CEP': '62011040',
        'ddd1': '88',
        'telefone1': '40033001',
        'ddd2': '',
        'telefone2': ''
    }
])

df['TELEFONE SOLICITADO'] = '11999999999'
df['OPERADORA DO TELEFONE'] = 'CLARO'

cols_to_drop = ['ddd1', 'telefone1', 'ddd2', 'telefone2', 't1_tipo', 't2_tipo', 'full_t1', 'full_t2']
df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

final_columns = [
    'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
    'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
    'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
]

expected_cols = {
    'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
    'CNPJ': 'CNPJ',
    'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
    'CNAE': 'CNAE',
    'LOGRADOURO': 'LOGRADOURO',
    'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA',
    'BAIRRO': 'BAIRRO',
    'CIDADE': 'CIDADE',
    'UF': 'UF',
    'CEP': 'CEP'
}

new_cols = {}
for c in df.columns:
    for k, v in expected_cols.items():
        if str(c).upper() == k.upper():
            new_cols[c] = v
df = df.rename(columns=new_cols)

sit_map = {
    '01': 'NULA',
    '02': 'ATIVA',
    '03': 'SUSPENSA',
    '04': 'INAPTA',
    '08': 'BAIXADA'
}
if 'SITUAÇÃO CADASTRAL' in df.columns:
    df['SITUAÇÃO CADASTRAL'] = df['SITUAÇÃO CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUAÇÃO CADASTRAL'])

for c in final_columns:
    if c not in df.columns: df[c] = ""
            
df = df[final_columns]

output_file = 'test_excel_output.xlsx'

with pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}}) as writer:
    chunk_size = 200000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i : i + chunk_size]
        chunk.to_excel(writer, sheet_name=f"Lote_{(i//chunk_size)+1}", index=False)

print("Created excel.")
