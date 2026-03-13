import os
import pandas as pd
import clickhouse_connect

UPLOAD_DIR = '/var/www/hemn_cloud/storage/uploads'

def diagnose():
    try:
        files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv') or f.endswith('.xlsx')]
        if not files:
            print('No Excel/CSV files found in upload dir.')
            return
        
        latest_file = max([os.path.join(UPLOAD_DIR, f) for f in files], key=os.path.getctime)
        print(f'Latest file: {latest_file}')
    except Exception as e:
        print(f'Error finding file: {e}')
        return

    try:
        # Read file
        if latest_file.endswith('.csv'):
            try:
                cep_df = pd.read_csv(latest_file, sep=';', dtype=str, on_bad_lines='skip')
                if len(cep_df.columns) == 1 and ',' in str(cep_df.columns[0]):
                    cep_df = pd.read_csv(latest_file, sep=',', dtype=str, on_bad_lines='skip')
            except Exception:
                cep_df = pd.read_csv(latest_file, sep=None, engine='python', dtype=str, on_bad_lines='skip')
        else:
            cep_df = pd.read_excel(latest_file, dtype=str)
            
        print(f'\nOriginal Columns in File: {cep_df.columns.tolist()}')
        
        cep_col = next((c for c in cep_df.columns if 'CEP' in str(c).upper()), None)
        num_col = next((c for c in cep_df.columns if 'NUM' in str(c).upper() or 'NÚM' in str(c).upper()), None)
        
        print(f'Detected CEP Column: {cep_col}, Detected NUM Column: {num_col}')
        
        if not cep_col:
            print('No CEP column detected :(')
            return
            
        # Clean data as the engine does
        raw_ceps = cep_df[cep_col].dropna().head(10).tolist()
        print(f'\nRaw CEPs from file: {raw_ceps}')
        
        cep_df[cep_col] = cep_df[cep_col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
        print(f'Cleaned CEPs: {cep_df[cep_col].dropna().head(10).tolist()}')
        
        raw_nums = []
        if num_col:
            raw_nums = cep_df[num_col].dropna().head(10).tolist()
            print(f'\nRaw Numbers from file: {raw_nums}')
            cep_df['num_match'] = cep_df[num_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper().str.lstrip('0')
            cep_df['num_match'] = cep_df['num_match'].apply(lambda x: x if x else '0')
            print(f"Cleaned Numbers: {cep_df['num_match'].dropna().head(10).tolist()}")
        
        # Query ClickHouse for the first 10 valid CEPs
        test_ceps = cep_df[cep_col].dropna().unique()
        test_ceps = test_ceps[test_ceps != '00nan000']
        test_ceps = test_ceps[test_ceps != '000nan00']
        test_ceps = test_ceps[:10]
        
        if len(test_ceps) == 0:
            print('No valid CEPs to test against DB!')
            return
            
        print(f'\nTesting ClickHouse with CEPs: {test_ceps}')
        
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='', database='hemn')
        
        cep_tuple = tuple(test_ceps) if len(test_ceps) > 1 else f"('{test_ceps[0]}')"
        
        # Check exactly for the first 50 pairs
        valid_pairs = cep_df[[cep_col, 'num_match']].drop_duplicates().rename(columns={cep_col: 'cep_sheet'})
        valid_pairs_list = valid_pairs.head(50).to_dict('records')
        where_conds = []
        for pair in valid_pairs_list:
            # SQL comparison simplified for diagnonis
            where_conds.append(f"(estab.cep = '{pair['cep_sheet']}')")
            
        where_clause = " OR ".join(where_conds)
        
        q_exact = f"""
            SELECT estab.cep as CEP, estab.numero as NUMERO_DA_FAIXADA, estab.cnpj_basico
            FROM hemn.estabelecimento estab
            WHERE {where_clause}
            LIMIT 1000
        """
        
        print(f'\nChecking ClickHouse for any record at these {len(valid_pairs_list)} CEPs...')
        res_exact = client.query(q_exact)
        ch_df_exact = pd.DataFrame(res_exact.result_rows, columns=res_exact.column_names)
        
        if ch_df_exact.empty:
            print("ZERO records found in DB for these CEPs.")
        else:
            ch_df_exact['_match_cep'] = ch_df_exact['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
            ch_df_exact['_match_num'] = ch_df_exact['NUMERO_DA_FAIXADA'].astype(str).str.strip().str.upper().str.lstrip('0')
            ch_df_exact['_match_num'] = ch_df_exact['_match_num'].apply(lambda x: x if x else '0')
            
            merged = ch_df_exact.merge(valid_pairs.rename(columns={'cep_sheet': '_match_cep', 'num_match': '_match_num'}), on=['_match_cep', '_match_num'], how='inner')
            
            if merged.empty:
                print(f"Found {len(ch_df_exact)} records at these CEPs, but NONE match the house numbers (lstrip-aware).")
                print("Samples in DB vs Samples in Sheet:")
                print("DB:", ch_df_exact[['_match_cep', '_match_num']].head(10).values.tolist())
                print("Sheet:", valid_pairs[['cep_sheet', 'num_match']].head(10).values.tolist())
            else:
                print(f"SUCCESS! Found {len(merged)} matches with lstrip-aware logic.")
                print(merged.head())
            print(ch_df)
            print('\nLet\'s see how Pandas cleans the ClickHouse numbers:')
            ch_df['CEP_match'] = ch_df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
            ch_df['num_match'] = ch_df['NUMERO_DA_FAIXADA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
            print(ch_df[['CEP_match', 'num_match']])
            
            # Simulate Merge
            print('\nSimulation of strictly Merge:')
            if num_col:
                valid_pairs = cep_df[[cep_col, 'num_match']].drop_duplicates().rename(columns={cep_col: 'cep_sheet'})
                merged = ch_df.merge(valid_pairs, left_on=['CEP_match', 'num_match'], right_on=['cep_sheet', 'num_match'], how='inner')
                print(merged)
            else:
                valid_ceps_df = cep_df[[cep_col]].drop_duplicates().rename(columns={cep_col: 'cep_sheet'})
                merged = ch_df.merge(valid_ceps_df, left_on='CEP_match', right_on='cep_sheet', how='inner')
                print(merged)

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnose()
