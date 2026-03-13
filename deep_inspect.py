import pandas as pd
import clickhouse_connect
import os
import re

def deep_inspect():
    # 1. Get latest CEARA file
    upload_dir = "/var/www/hemn_cloud/storage/uploads"
    files = [f for f in os.listdir(upload_dir) if "CEARA" in f]
    if not files:
        print("No CEARA files found")
        return
    latest = max([os.path.join(upload_dir, f) for f in files], key=os.path.getctime)
    print(f"Inspecting file: {latest}")

    # 2. Read CSV
    try:
        cep_df = pd.read_csv(latest, sep=None, engine='python', dtype=str, on_bad_lines='skip')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    cep_col = next((c for c in cep_df.columns if "CEP" in str(c).upper()), None)
    num_col = next((c for c in cep_df.columns if "NUMERO" in str(c).upper().replace('Ú', 'U')), None)

    if not cep_col or not num_col:
        print(f"Columns not found. Found: {cep_df.columns.tolist()}")
        return

    # 3. Clean CSV data as the engine does
    local_df = cep_df.dropna(subset=[cep_col, num_col]).copy()
    local_df['_match_cep'] = local_df[cep_col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    local_df['_match_num'] = local_df[num_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper().str.lstrip('0')
    local_df['_match_num'] = local_df['_match_num'].apply(lambda x: x if x else '0')
    
    valid_ceps = local_df['_match_cep'].unique().tolist()
    print(f"Found {len(valid_ceps)} unique valid CEPs in sheet.")

    # 4. Connect to ClickHouse
    client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
    
    # 5. Query ALL records for the first 100 CEPs
    sample_ceps = valid_ceps[:100]
    q = f"SELECT cep, numero FROM hemn.estabelecimento WHERE cep IN {tuple(sample_ceps)} LIMIT 10000"
    res = client.query(q)
    db_df = pd.DataFrame(res.result_rows, columns=res.column_names)

    if db_df.empty:
        print(f"ZERO records found in DB for CEPs sample.")
        return

    print(f"\nFound {len(db_df)} records in DB for these CEPs.")
    
    # 6. Normalize DB data as the engine does
    db_df['_match_cep'] = db_df['cep'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
    db_df['_match_num'] = db_df['numero'].astype(str).str.strip().str.upper().str.lstrip('0')
    db_df['_match_num'] = db_df['_match_num'].apply(lambda x: x if x else '0')

    # 7. Match
    sheet_samples = local_df[local_df['_match_cep'].isin(sample_ceps)][['_match_cep', '_match_num']].drop_duplicates()
    
    # NEW logic: Try to strip CEP from Number if Number starts with CEP
    def strip_cep_from_num(row):
        num = str(row['_match_num'])
        cep = str(row['_match_cep'])
        if num.startswith(cep) and len(num) > len(cep):
            return num[len(cep):].lstrip('0')
        return num
        
    sheet_samples['_match_num_stripped'] = sheet_samples.apply(strip_cep_from_num, axis=1)
    
    matches = db_df.merge(sheet_samples.rename(columns={'_match_num': 'original_num', '_match_num_stripped': '_match_num'}), on=['_match_cep', '_match_num'], how='inner')
    print(f"Matches found WITH prefix stripping: {len(matches)}")

    if len(matches) == 0:
        print("\nDIAGNOSIS: Still zero matches even with prefix stripping.")
        # Find a CEP that exists in DB
        some_cep = db_df['_match_cep'].iloc[0]
        db_nums = db_df[db_df['_match_cep'] == some_cep]['numero'].tolist()
        sheet_nums = sheet_samples[sheet_samples['_match_cep'] == some_cep]['_match_num'].tolist()
        print(f"CEP: {some_cep}")
        print(f"DB Raw Numbers: {db_nums[:10]}")
        print(f"Sheet Normalized Numbers: {sheet_nums[:10]}")
        
    else:
        print("\nSample matches found!")
        print(matches.head())

if __name__ == "__main__":
    deep_inspect()
