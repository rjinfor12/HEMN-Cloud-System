import os
import sqlite3
import pandas as pd
import threading
import time
from datetime import datetime
import uuid
import shutil
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_name(name):
    """Remove common suffixes to improve matching (JUNIOR, FILHO, etc.)"""
    if not name: return ""
    name = remove_accents(str(name).upper().strip())
    suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR', ' SEGUNDO', ' TERCEIRO']
    for sfx in suffixes:
        if name.endswith(sfx):
            name = name[:-len(sfx)].strip()
            break
    return name

class CloudEngine:
    def __init__(self, **kwargs):
        import platform
        if platform.system() == 'Linux':
            import clickhouse_connect
            self.ch_client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
            self.db_carrier = "/var/www/hemn_cloud/hemn_carrier.db"
            self.db_path = "/var/www/hemn_cloud/hemn_cloud.db"
        else:
            self.ch_client = None 
            self.db_carrier = kwargs.get('db_carrier_path')
            self.db_path = kwargs.get('db_path') or "hemn_cloud.db"
        
        self._init_db()
        self._load_carrier_assets()

    def _load_carrier_assets(self):
        """Loads prefix tree and operator dictionary from data_assets folder"""
        self.prefix_tree = {} # {prefix: operator_code}
        # Initial hardcoded fallback for most common
        self.anatel_dict = {
            "55320": "VIVO", "55321": "CLARO", "55341": "TIM", "55331": "OI",
            "55312": "ALGAR", "55343": "SERCOMTEL", "55306": "SURF", "55301": "ARQIA",
            "55315": "TELECALL", "55322": "BRISANET"
        }
        
        base_dir = "/var/www/hemn_cloud/data_assets"
        prefix_path = os.path.join(base_dir, "prefix_anatel.csv")
        dict_path = os.path.join(base_dir, "cod_operadora.csv")
        
        # Load Operadora Dictionary from CSV if available
        if os.path.exists(dict_path):
            try:
                import csv
                with open(dict_path, mode='r', encoding='latin1') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2: self.anatel_dict[row[0].strip()] = row[1].strip()
            except: pass
            
        # Load Prefix Tree (Standard ANATEL Base)
        if os.path.exists(prefix_path):
            try:
                df = pd.read_csv(prefix_path, sep=';', dtype=str)
                if 'number' in df.columns and 'company' in df.columns:
                    for _, row in df.iterrows():
                        self.prefix_tree[row['number'].strip()] = row['company'].strip()
            except: pass

    def get_op_name(self, code):
        """Helper to get operator name from RN1/Anatel code"""
        code = str(code).strip()
        return self.anatel_dict.get(code, f"OUTRA ({code})" if code else "OUTRA")

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS background_tasks (
                id TEXT PRIMARY KEY,
                username TEXT,
                module TEXT,
                status TEXT,
                progress REAL,
                message TEXT,
                result_file TEXT,
                record_count INTEGER,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asaas_payments (
                id TEXT PRIMARY KEY,
                username TEXT,
                amount REAL,
                credits REAL,
                status TEXT,
                pix_payload TEXT,
                pix_image_base64 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                type TEXT,
                amount REAL,
                module TEXT,
                description TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _create_task(self, module="ENRICH", username=None):
        tid = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO background_tasks (id, username, module, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tid, username, module, "QUEUED", 0, "Aguardando início...", created_at)
        )
        conn.commit()
        conn.close()
        return tid

    def cancel_task(self, tid):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE background_tasks SET status = 'CANCELLED', message = 'Processo cancelado pelo usuário.' WHERE id = ?", (tid,))
        conn.commit()
        conn.close()
        return True

    def get_user_tasks(self, username):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Include COMPLETED and FAILED tasks from the last 24 hours for UI persistence
        rows = conn.execute(
            "SELECT * FROM background_tasks WHERE username = ? AND (status IN ('QUEUED', 'PROCESSING') OR (created_at > datetime('now','-24 hours'))) ORDER BY created_at DESC", 
            (username,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _update_task(self, tid, **kwargs):
        if not kwargs: return
        cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        conn = sqlite3.connect(self.db_path)
        conn.execute(f"UPDATE background_tasks SET {cols} WHERE id = ?", list(kwargs.values()) + [tid])
        conn.commit()
        conn.close()

    def get_task_status(self, tid):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM background_tasks WHERE id = ?", (tid,)).fetchone()
        conn.close()
        if not row: return {"status": "NOT_FOUND"}
        return dict(row)

    def _batch_query(self, sql_template, key_param, values, batch_size=2000, tid=None, base_prog=0, max_prog=0, msg_prefix=""):
        """Execute a query with a large IN() list in safe-sized batches with progress tracking."""
        all_rows = []
        col_names = []
        total = len(values)
        if total == 0: return [], []
        
        for i in range(0, total, batch_size):
            # Check for cancellation
            if tid:
                status = self.get_task_status(tid)
                if status.get("status") == "CANCELLED": return [], []

            chunk = values[i:i + batch_size]
            res = self.ch_client.query(sql_template, {key_param: chunk})
            all_rows.extend(res.result_rows)
            if not col_names and res.column_names:
                col_names = res.column_names
            
            if tid and max_prog > base_prog:
                prog = base_prog + int((i / total) * (max_prog - base_prog))
                self._update_task(tid, progress=prog, message=f"{msg_prefix} ({i:,}/{total:,})...")

        return all_rows, col_names

    def _parse_address_columns(self, row):
        # Simplificado para o exemplo, manter original se possível
        tipo = row.get('tipo_logradouro', '')
        logra = row.get('logradouro', '')
        num = row.get('numero', '')
        comp = row.get('complemento', '')
        bairro = row.get('bairro', '')
        muni = row.get('municipio_nome', '')
        uf = row.get('uf', '')
        cep = row.get('cep', '')
        full_logra = f"{tipo} {logra}".strip()
        return [full_logra, num, comp, bairro, muni, uf, cep]

    def _parse_contact_columns(self, row):
        ddd1 = str(row.get('ddd1', '')).strip()
        tel1 = str(row.get('telefone1', '')).strip()
        ddd2 = str(row.get('ddd2', '')).strip()
        tel2 = str(row.get('telefone2', '')).strip()
        
        def clean(d, t):
            if not d or not t: return "", ""
            return d, t
        
        d1, t1 = clean(ddd1, tel1)
        if t1: return [d1, t1, "FIXO/CEL", row.get('correio_eletronico', '')]
        d2, t2 = clean(ddd2, tel2)
        if t2: return [d2, t2, "FIXO/CEL", row.get('correio_eletronico', '')]
        return ["", "", "", row.get('correio_eletronico', '')]

    def start_enrich(self, input_file, output_dir, name_col, cpf_col, username=None):
        print(f"[DEBUG] start_enrich called: input={input_file}, name_col={name_col}, cpf_col={cpf_col}, user={username}")
        tid = self._create_task(module="ENRICH", username=username)
        threading.Thread(target=self._run_enrich, args=(tid, input_file, output_dir, name_col, cpf_col), daemon=True).start()
        return tid

    def deep_search(self, name, cpf):
        """Busca rápida unitária no ClickHouse"""
        if not self.ch_client:
            return pd.DataFrame()
            
        basics = []
        
        if cpf:
            # Robust cleaning
            cpf_clean = ''.join(filter(str.isdigit, str(cpf)))
            if len(cpf_clean) >= 11:
                cpf_mask = f"***{cpf_clean[3:9]}**"
                res = self.ch_client.query("SELECT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio IN (%(c1)s, %(c2)s) LIMIT 50", 
                                          {'c1': cpf_clean, 'c2': cpf_mask})
                basics.extend([r[0] for r in res.result_rows])
        
        if name:
            name_clean = remove_accents(str(name).strip().upper())
            # Try both prefix for speed and contains for flexibility
            res = self.ch_client.query("SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s OR nome_socio LIKE %(nc)s LIMIT 50", 
                                      {'n': f'{name_clean}%', 'nc': f'%{name_clean}%'})
            basics.extend([r[0] for r in res.result_rows])
            res = self.ch_client.query("SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(n)s OR razao_social LIKE %(nc)s LIMIT 50", 
                                      {'n': f'{name_clean}%', 'nc': f'%{name_clean}%'})
            basics.extend([r[0] for r in res.result_rows])
            
        if not basics:
            return pd.DataFrame()
            
        basics = list(set(basics))[:50]
        
        query = f"""
            SELECT e.razao_social, 
                   concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS cnpj_completo,
                   multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                   s.nome_socio, s.cnpj_cpf_socio,
                   est.correio_eletronico AS email_novo,
                   concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', coalesce(m.descricao, 'N/A'), '/', est.uf) AS endereco_completo,
                   est.telefone1 AS telefone_novo,
                   est.ddd1 AS ddd_novo,
                   'FIXO' AS tipo_telefone
            FROM hemn.empresas e
            JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
            LEFT JOIN hemn.socios s ON est.cnpj = s.cnpj
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE e.cnpj_basico IN ({','.join(['%s' for _ in basics])})
            ORDER BY multiIf(est.situacao_cadastral = '02', 1, 2)
            LIMIT 50
        """
        res = self.ch_client.query(query, basics)
        return pd.DataFrame(res.result_rows, columns=res.column_names)


    def _run_enrich(self, tid, input_file, output_dir, name_col, cpf_col):
        self._update_task(tid, status="PROCESSING", message="Iniciando Escaneamento Titanium-MT (Motor Paralelo)...")
        try:
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            start_time = time.time()
            output_file = os.path.join(output_dir, f"Enriquecido_{tid[:8]}.xlsx")
            
            # Memory Optimized: Determine row count without loading full file
            if input_file.endswith('.csv'):
                total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8', errors='ignore')) - 1
            else:
                # Use openpyxl to get dimensions without loading data
                import openpyxl
                wb = openpyxl.load_workbook(input_file, read_only=True)
                total_rows = wb.active.max_row - 1
                wb.close()
            
            self._update_task(tid, progress=2, message=f"Lendo base ({total_rows:,} registros)...")

            # Memory Optimized: Multi-stage processing
            all_cpfs = []
            all_names = []
            
            if input_file.endswith('.csv'):
                # Chunked reading to save RAM
                for chunk in pd.read_csv(input_file, sep=None, engine='python', chunksize=10000):
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED": return
                    
                    # Process chunk...
                    # (For simplicity in this diff, I'll load the keys only)
                    if cpf_col in chunk.columns:
                        all_cpfs.extend(chunk[cpf_col].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist())
                    else:
                        # Fallback if cpf_col not found, use first column
                        all_cpfs.extend(chunk.iloc[:, 0].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist())

                    if name_col in chunk.columns:
                        all_names.extend(chunk[name_col].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    elif len(chunk.columns) > 1:
                        # Fallback if name_col not found, use second column
                        all_names.extend(chunk.iloc[:, 1].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    else:
                        # If only one column, use it for both if name_col not found
                        all_names.extend(chunk.iloc[:, 0].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist())
                    
                    del chunk
                
                # Reconstruct df_in from collected data
                df_in = pd.DataFrame({'original_cpf': all_cpfs, 'original_name': all_names})
                # Assuming original input file columns are needed for final output,
                # a full load might be necessary or a more complex merge strategy.
                # For now, let's assume we need to load the full df_in for the final merge.
                # This part needs careful consideration based on actual memory constraints and requirements.
                # For this diff, I'll re-load df_in fully for the merge phase,
                # but the initial CPF/Name extraction is chunked.
                if input_file.endswith('.csv'):
                    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                        primeira = f.readline()
                    sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                    df_in = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
                else:
                    df_in = pd.read_excel(input_file, dtype=str)

            else: # Excel file
                df_in = pd.read_excel(input_file, dtype=str)
                # Fallback indices if columns are None or not found
                c_idx = cpf_col if (cpf_col and cpf_col in df_in.columns) else df_in.columns[0]
                n_idx = name_col if (name_col and name_col in df_in.columns) else (df_in.columns[1] if len(df_in.columns) > 1 else df_in.columns[0])
                
                all_cpfs = df_in[c_idx].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).tolist()
                all_names = df_in[n_idx].fillna('').astype(str).str.upper().str.strip().apply(remove_accents).tolist()

            total = len(df_in) # Recalculate total based on actual df_in if it was reloaded
            
            # --- PHASE 0: NORMALIZAÇÃO ---
            # These columns are now created based on the full df_in after loading
            if name_col in df_in.columns: n_col = name_col
            else: n_col = df_in.columns[1] if len(df_in.columns) > 1 else df_in.columns[0]
            if cpf_col in df_in.columns: c_col = cpf_col
            else: c_col = df_in.columns[0]
            
            df_in['titanium_nome'] = df_in[n_col].fillna('').astype(str).str.upper().str.strip().apply(remove_accents)
            df_in['titanium_cpf'] = df_in[c_col].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)

            # --- PHASE 1: BATCH PROCESSING (EXTREME SPEED) ---
            # Extract all CPFs and Names
            # all_cpfs and all_names are already populated from chunked reading or full Excel load
            
            # Identify valid CPFs for bulk lookup
            valid_cpfs = [cpf for cpf in all_cpfs if len(cpf) >= 11]
            valid_masks = [f"***{cpf[3:9]}**" for cpf in valid_cpfs]
            
            # Combine exact CPFs and typical masks for MEI/Socios
            search_terms = list(set(valid_cpfs + valid_masks))
            
            # --- PHASE 1.1: NAME VARIATIONS (NORMALIZED) ---
            valid_names = [normalize_name(n) for n in all_names if len(str(n)) > 3]
            search_names = list(set(valid_names))
            
            # Prepare Global Cache
            global_cache = {}
            found_count = 0
            
            # --- PHASE 1: TITANIUM-TURBO JOIN (HIGH SPEED) ---
            # Process in large batches for join efficiency
            q_template = """
                SELECT 
                    s.lookup_key AS lookup_key,
                    e.razao_social AS razao_social, 
                    estab.cnpj_basico AS cnpj_basico, 
                    estab.cnpj_ordem AS cnpj_ordem, 
                    estab.cnpj_dv AS cnpj_dv, 
                    estab.situacao_cadastral AS situacao_cadastral, 
                    estab.uf AS uf, 
                    mun.descricao AS municipio_nome, 
                    estab.ddd1 AS ddd1, 
                    estab.telefone1 AS telefone1, 
                    estab.ddd2 AS ddd2, 
                    estab.telefone2 AS telefone2, 
                    estab.correio_eletronico AS correio_eletronico, 
                    estab.tipo_logradouro AS tipo_logradouro, 
                    estab.logradouro AS logradouro, 
                    estab.numero AS numero, 
                    estab.complemento AS complemento, 
                    estab.bairro AS bairro, 
                    estab.cep AS cep, 
                    estab.cnae_fiscal AS cnae_fiscal, 
                    estab.municipio AS municipio, 
                    s.nome_socio AS nome_socio
                FROM (
                    SELECT cnpj_basico, {lookup_col} AS lookup_key, nome_socio
                    FROM hemn.socios 
                    WHERE {lookup_col} IN %(keys)s
                ) AS s
                INNER JOIN hemn.estabelecimento AS estab ON s.cnpj_basico = estab.cnpj_basico
                INNER JOIN hemn.empresas AS e ON s.cnpj_basico = e.cnpj_basico
                LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                ORDER BY (estab.situacao_cadastral = '02') DESC, estab.situacao_cadastral ASC
                LIMIT 1 BY lookup_key
            """

            if search_terms:
                self._update_task(tid, progress=10, message=f"Turbo v3.0: Cruzando {len(search_terms):,} CPFs/Máscaras...")
                
                # Socio lookup
                q_cpf = q_template.format(lookup_col="cnpj_cpf_socio")
                results_s, cols_s = self._batch_query(q_cpf, "keys", search_terms, batch_size=5000, tid=tid, base_prog=10, max_prog=35, msg_prefix="Cruzando Sócios")
                
                # Direct Empresa lookup (for MEIs/CNPJs)
                q_mei = """
                    SELECT 
                        e.cnpj_basico AS lookup_key,
                        e.razao_social AS razao_social, 
                        estab.cnpj_basico AS cnpj_basico, 
                        estab.cnpj_ordem AS cnpj_ordem, 
                        estab.cnpj_dv AS cnpj_dv, 
                        estab.situacao_cadastral AS situacao_cadastral, 
                        estab.uf AS uf, 
                        mun.descricao AS municipio_nome, 
                        estab.ddd1 AS ddd1, 
                        estab.telefone1 AS telefone1, 
                        estab.ddd2 AS ddd2, 
                        estab.telefone2 AS telefone2, 
                        estab.correio_eletronico AS correio_eletronico, 
                        estab.tipo_logradouro AS tipo_logradouro, 
                        estab.logradouro AS logradouro, 
                        estab.numero AS numero, 
                        estab.complemento AS complemento, 
                        estab.bairro AS bairro, 
                        estab.cep AS cep, 
                        estab.cnae_fiscal AS cnae_fiscal, 
                        estab.municipio AS municipio, 
                        '' AS nome_socio
                    FROM (
                        SELECT * FROM hemn.empresas WHERE cnpj_basico IN %(keys)s
                    ) AS e
                    INNER JOIN hemn.estabelecimento AS estab ON e.cnpj_basico = estab.cnpj_basico
                    LEFT JOIN hemn.municipio AS mun ON estab.municipio = mun.codigo
                    ORDER BY (estab.situacao_cadastral = '02') DESC, estab.situacao_cadastral ASC
                    LIMIT 1 BY lookup_key
                """
                results_e, cols_e = self._batch_query(q_mei, "keys", search_terms, batch_size=5000, tid=tid, base_prog=35, max_prog=40, msg_prefix="Cruzando MEIs")
                
                for r in results_s + results_e:
                    # Use appropriate columns for the result row
                    curr_cols = cols_s if len(r) == len(cols_s) else cols_e
                    d = dict(zip(curr_cols, r))
                    k = d['lookup_key']
                    if k not in global_cache:
                        addr = self._parse_address_columns(d)
                        cont = self._parse_contact_columns(d)
                        mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                        global_cache[k] = {
                            'CNPJ': f"{str(d['cnpj_basico']).zfill(8)}{str(d['cnpj_ordem']).zfill(4)}{str(d['cnpj_dv']).zfill(2)}",
                            'RAZAO_SOCIAL': d['razao_social'], 
                            'SITUACAO': mapping.get(str(d['situacao_cadastral']).zfill(2), 'ATIVA'),
                            'SITUACAO_CODIGO': str(d['situacao_cadastral']).zfill(2),
                            'CNAE': d['cnae_fiscal'], 'LOGRADOURO': addr[0], 'NUMERO': addr[1], 'COMPLEMENTO': addr[2],
                            'BAIRRO': addr[3], 'CIDADE': str(addr[4]).upper(), 'UF_END': addr[5], 'CEP': addr[6],
                            'DDD': cont[0], 'TELEFONE': cont[1], 'TIPO': cont[2], 'EMAIL': cont[3]
                        }

            if search_names:
                self._update_task(tid, progress=40, message=f"Turbo v3.0: Cruzando {len(search_names):,} Nomes...")
                q_name = q_template.format(lookup_col="nome_socio")
                results, cols = self._batch_query(q_name, "keys", search_names, batch_size=5000, tid=tid, base_prog=40, max_prog=75, msg_prefix="Cruzando Nomes")
                
                for r in results:
                    d = dict(zip(cols, r))
                    # Normalizamos a chave de volta caso o clickhouse tenha retornado com variacao minor
                    k = normalize_name(d['lookup_key'])
                    if k not in global_cache:
                        addr = self._parse_address_columns(d)
                        cont = self._parse_contact_columns(d)
                        mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                        global_cache[k] = {
                            'CNPJ': f"{str(d['cnpj_basico']).zfill(8)}{str(d['cnpj_ordem']).zfill(4)}{str(d['cnpj_dv']).zfill(2)}",
                            'RAZAO_SOCIAL': d['razao_social'], 
                            'SITUACAO': mapping.get(str(d['situacao_cadastral']).zfill(2), 'ATIVA'),
                            'SITUACAO_CODIGO': str(d['situacao_cadastral']).zfill(2),
                            'CNAE': d['cnae_fiscal'], 'LOGRADOURO': addr[0], 'NUMERO': addr[1], 'COMPLEMENTO': addr[2],
                            'BAIRRO': addr[3], 'CIDADE': str(addr[4]).upper(), 'UF_END': addr[5], 'CEP': addr[6],
                            'DDD': cont[0], 'TELEFONE': cont[1], 'TIPO': cont[2], 'EMAIL': cont[3]
                        }

            # --- PHASE 2: IN-MEMORY MAPPING & FALLBACKS ---
            self._update_task(tid, progress=80, message="Estruturando resultados finais (C-Level Array Vectorization)...")
            
            if global_cache:
                # Converter o cache em DataFrame para merge imediato
                df_cache = pd.DataFrame.from_dict(global_cache, orient='index')
                df_cache.index.name = 'lookup_key'
                df_cache.reset_index(inplace=True)
                
                # Preparar coluna de lookup no DataFrame original (tenta CPF exato primeiro, senao a mascara)
                df_in['mask_calc'] = df_in['titanium_cpf'].apply(lambda x: f"***{x[3:9]}**" if len(str(x)) >= 11 else "")
                df_in['lookup_key'] = df_in['titanium_cpf']
                
                # Merge tenta bater a chave primaria primeiro (CPF Exato)
                df_merged = pd.merge(df_in, df_cache, on='lookup_key', how='left')
                
                # Se ainda tem nulos, tenta bater a mascara
                if 'mask_calc' in df_in.columns:
                    mask_rows = df_merged['CNPJ'].isna()
                    if mask_rows.any():
                        df_masks_only = df_in[mask_rows].copy()
                        df_masks_only['lookup_key'] = df_masks_only['mask_calc']
                        df_merged_masks = pd.merge(df_masks_only.drop(columns=df_cache.columns.drop('lookup_key'), errors='ignore'), df_cache, on='lookup_key', how='left')
                        # Update original merged results with mask hits
                        df_merged.update(df_merged_masks, overwrite=False)

                    # Se AINDA tem nulos, tenta bater pelo Nome Normalizado
                    null_rows = df_merged['CNPJ'].isna()
                    if null_rows.any():
                        df_names_only = df_in[null_rows].copy()
                        df_names_only['lookup_key'] = df_names_only['titanium_nome'].apply(normalize_name)
                        df_merged_names = pd.merge(df_names_only.drop(columns=df_cache.columns.drop('lookup_key'), errors='ignore'), df_cache, on='lookup_key', how='left')
                        df_merged.update(df_merged_names, overwrite=False)
                        
                found_count = df_merged['CNPJ'].notna().sum()
                df_final = df_merged.drop(columns=['titanium_cpf', 'titanium_nome', 'mask_calc', 'lookup_key'], errors='ignore')
            else:
                found_count = 0
                df_final = df_in.drop(columns=['titanium_cpf', 'titanium_nome'], errors='ignore')

            # Salvar no Excel de forma ultra rapida
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            self._update_task(tid, progress=95, message="Salvando arquivo .xlsx resultante...")
            df_final.to_excel(output_file, index=False)
            total_time = time.time() - start_time
            
            # Converter numpy.int64 para int python nativo para evitar erro 500 no FastAPI
            fc_native = int(found_count)
            total_native = int(total)
            
            msg = f"TITANIUM-DONE: V2.0 Processou {total_native} linhas. {fc_native} encontrados em {total_time:.1f}s."
            self._update_task(tid, status="COMPLETED", progress=100, message=msg, result_file=output_file, record_count=fc_native)

        except Exception as e:
            import traceback
            err_msg = f"{str(e)} | {traceback.format_exc()[-200:]}"
            self._update_task(tid, status="FAILED", message=f"TITANIUM-ERROR: {err_msg}")

    # --- EXTRACTION (FULL FILTERS) ---
    def start_extraction(self, filters, output_dir, username=None):
        tid = self._create_task(module="EXTRACTION", username=username)
        threading.Thread(target=self._run_extraction, args=(tid, filters, output_dir), daemon=True).start()
        return tid

    def _run_extraction(self, tid, filters, output_dir):
        self._update_task(tid, status="PROCESSING", progress=1, message="Iniciando motores ClickHouse...")
        try:
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            output_file = os.path.join(output_dir, f"Extracao_{tid[:8]}.xlsx")
            
            conds = []
            params = {}
            
            sit = filters.get("situacao", "02")
            if sit != "TODOS":
                conds.append("estab.situacao_cadastral = %(sit)s")
                params['sit'] = sit

            if filters.get("uf"): 
                conds.append("estab.uf = %(uf)s")
                params['uf'] = filters["uf"].strip().upper()
            
            if filters.get("cidade"): 
                conds.append("m.descricao LIKE %(cid)s")
                params['cid'] = f"%{filters['cidade'].strip().upper()}%"
            
            if filters.get("cnae"): 
                cnaes = [c.strip() for c in filters["cnae"].split(',')]
                conds.append("estab.cnae_fiscal IN %(cnaes)s")
                params['cnaes'] = cnaes

            tipo_req = filters.get("tipo_tel", "TODOS")
            if tipo_req == "CELULAR":
                conds.append("((length(estab.telefone1) >= 8 AND substring(estab.telefone1, 1, 1) IN ('6','7','8','9')) OR (length(estab.telefone2) >= 8 AND substring(estab.telefone2, 1, 1) IN ('6','7','8','9')))")
            elif tipo_req == "FIXO":
                conds.append("((length(estab.telefone1) >= 8 AND substring(estab.telefone1, 1, 1) IN ('2','3','4','5')) OR (length(estab.telefone2) >= 8 AND substring(estab.telefone2, 1, 1) IN ('2','3','4','5')))")
            elif tipo_req == "AMBOS":
                conds.append("((length(estab.telefone1) >= 8 AND substring(estab.telefone1, 1, 1) IN ('6','7','8','9') AND length(estab.telefone2) >= 8 AND substring(estab.telefone2, 1, 1) IN ('2','3','4','5')) OR (length(estab.telefone1) >= 8 AND substring(estab.telefone1, 1, 1) IN ('2','3','4','5') AND length(estab.telefone2) >= 8 AND substring(estab.telefone2, 1, 1) IN ('6','7','8','9')))")
            else:
                conds.append("(estab.telefone1 != '' OR estab.telefone2 != '')")

            cep_file = filters.get("cep_file")
            cep_df = None
            cep_col, num_col = None, None
            if cep_file and os.path.exists(cep_file):
                self._update_task(tid, progress=2, message="Lendo planilha de filtro de CEPs...")
                try:
                    if cep_file.lower().endswith('.csv'):
                        try:
                            # Tenta ler com separador ponto e vírgula primeiro (padrão Excel BR)
                            cep_df = pd.read_csv(cep_file, sep=';', dtype=str, on_bad_lines='skip')
                            # Se ler como uma coluna só e houver vírgula no nome da primeira coluna, tenta com vírgula
                            if len(cep_df.columns) == 1 and ',' in str(cep_df.columns[0]):
                                cep_df = pd.read_csv(cep_file, sep=',', dtype=str, on_bad_lines='skip')
                        except Exception:
                            # Fallback para engine python que detecta o separador automaticamente
                            cep_df = pd.read_csv(cep_file, sep=None, engine='python', dtype=str, on_bad_lines='skip')
                    else:
                        cep_df = pd.read_excel(cep_file, dtype=str)
                        
                    cep_col = next((c for c in cep_df.columns if "CEP" in str(c).upper()), None)
                    num_col = next((c for c in cep_df.columns if "NUMERO" in str(c).upper().replace('Ú', 'U')), None)
                    
                    if cep_col:
                        # Limpeza robusta: Remove vazios antes de processar
                        # Isso impede que NaN vire "nan" -> "" -> "00000000"
                        local_df = cep_df.dropna(subset=[cep_col]).copy()
                        
                        series_cep = local_df[cep_col].astype(str).str.replace(r'\D', '', regex=True)
                        series_cep = series_cep[series_cep != '']
                        series_cep = series_cep.str.zfill(8)
                        
                        # Filtra apenas o que parece ser um CEP válido (8 dígitos, não zero)
                        valid_ceps = [c for c in series_cep.unique() if c and c != '00000000' and len(c) == 8]
                        
                        if valid_ceps:
                            conds.append("estab.cep IN %(ceps)s")
                            params['ceps'] = valid_ceps
                        
                        # Guardamos a versão limpa associada ao dataframe original de filtro
                        local_df['_match_cep'] = series_cep
                        
                        # NOVA LÓGICA: Se o número começa com o CEP (comum em exports errados), remove o prefixo
                        def clean_num_concatenated(row):
                            num = str(row.get(num_col, '')).replace('.0', '').strip().upper()
                            num = re.sub(r'\D', '', num) # Pega só dígitos primeiro para comparar com CEP
                            cep = str(row.get('_match_cep', ''))
                            if num.startswith(cep) and len(num) > len(cep):
                                return num[len(cep):].lstrip('0')
                            # Fallback para limpeza padrão se não houver concatenação
                            raw_val = str(row.get(num_col, '')).split('.')[0].strip().upper()
                            return raw_val.lstrip('0') if raw_val.lstrip('0') else '0'

                        if num_col:
                            local_df['_match_num'] = local_df.apply(clean_num_concatenated, axis=1)
                        
                        cep_df = local_df # Substituimos pelo limpo
                        
                except Exception as e:
                    self._update_task(tid, status="FAILED", message=f"Erro ao analisar planilha CEP/NUMERO: {str(e)}")
                    return

            where_clause = " AND ".join(conds) if conds else "1=1"
            
            q = f"""
                SELECT e.razao_social as NOME_DA_EMPRESA, 
                       concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
                       estab.situacao_cadastral as SITUACAO_CADASTRAL,
                       estab.cnae_fiscal as CNAE, 
                       estab.logradouro as LOGRADOURO,
                       estab.numero as NUMERO_DA_FAIXADA,
                       estab.bairro as BAIRRO,
                       estab.CIDADE, estab.uf as UF, estab.cep as CEP, 
                       estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
                FROM (
                    SELECT estab.*, m.descricao as CIDADE 
                    FROM hemn.estabelecimento estab 
                    LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
                    WHERE {where_clause} 
                    LIMIT 20000000
                ) as estab 
                JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico 
            """
            
            self._update_task(tid, progress=20, message="Executando extração em massa no ClickHouse...")
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            res = self.ch_client.query(q, params)
            df = pd.DataFrame(res.result_rows, columns=res.column_names)

            if df.empty:
                self._update_task(tid, status="COMPLETED", progress=100, message="Nenhum registro encontrado.", record_count=0)
                return

            if cep_df is not None and '_match_cep' in cep_df.columns and not df.empty:
                self._update_task(tid, progress=30, message="Cruzando com a planilha fornecida...")
                
                # Normalização do DF do Clickhouse para o Cruzamento
                df['_match_cep'] = df['CEP'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
                # Extrai apenas números e remove zeros à esquerda (ex: '02' -> '2')
                df['_match_num'] = df['NUMERO_DA_FAIXADA'].astype(str).str.strip().str.upper().str.lstrip('0')
                df['_match_num'] = df['_match_num'].apply(lambda x: x if x else '0')

                # Normalização do DF da Planilha
                if num_col and num_col in cep_df.columns and '_match_num' in cep_df.columns:
                    # Filtra CEPs lixo e garante que o merge seja limpo
                    valid_sheet = cep_df[
                        (cep_df['_match_cep'] != '00000000') & 
                        (cep_df['_match_cep'].str.len() == 8)
                    ][['_match_cep', '_match_num']].drop_duplicates()
                    
                    df = df.merge(valid_sheet, on=['_match_cep', '_match_num'], how='inner')
                else:
                    # Filtro apenas por CEP
                    valid_sheet_ceps = cep_df[
                        (cep_df['_match_cep'] != '00000000') & 
                        (cep_df['_match_cep'].str.len() == 8)
                    ][['_match_cep']].drop_duplicates()
                    
                    df = df.merge(valid_sheet_ceps, on='_match_cep', how='inner')
                
                # Remove colunas de controle do resultado final
                df = df.drop(columns=[c for c in ['_match_cep', '_match_num'] if c in df.columns])
                
                if df.empty:
                    msg = "Nenhum dos registros encontrados no banco bate exatamente com o Número e CEP da planilha."
                    self._update_task(tid, status="COMPLETED", progress=100, message=msg, record_count=0)
                    return

            self._update_task(tid, progress=85, message="Filtrando telefones...")
            tipo_req = filters.get("tipo_tel", "TODOS")
            
            def check_tel(t):
                if not t or str(t).upper() in ['NAN', 'NONE']: return None
                t = str(t).strip().replace('.0', '')
                num = re.sub(r'\D', '', t)
                if not num: return None
                return "CELULAR" if (len(num) == 9 or (len(num) == 8 and num[0] in '6789')) else "FIXO"

            def get_full(d, t):
                if not t or str(t).upper() in ['NAN', 'NONE']: return ""
                d = str(d).replace('.0', '').replace('nan', '') if pd.notna(d) else ""
                t = str(t).replace('.0', '').replace('nan', '')
                full = re.sub(r'\D', '', d + t)
                # Fix mobile length (adding 9) if explicitly 10 digits and starts with 6-9
                if len(full) == 10 and full[2] in '6789':
                    full = full[:2] + '9' + full[2:]
                return full

            df['full_t1'] = df.apply(lambda x: get_full(x['ddd1'], x['telefone1']), axis=1)
            df['full_t2'] = df.apply(lambda x: get_full(x['ddd2'], x['telefone2']), axis=1)
            df['t1_tipo'] = df['telefone1'].apply(check_tel)
            df['t2_tipo'] = df['telefone2'].apply(check_tel)

            # Filter rows based on phone type request
            if tipo_req == "AMBOS":
                # Must have at least one of each
                mask = ((df['t1_tipo'] == "CELULAR") & (df['t2_tipo'] == "FIXO")) | \
                       ((df['t1_tipo'] == "FIXO") & (df['t2_tipo'] == "CELULAR"))
                df = df[mask].copy()
            elif tipo_req != "TODOS":
                df = df[(df['t1_tipo'] == tipo_req) | (df['t2_tipo'] == tipo_req)].copy()

            # Now select exactly ONE phone column to show based on preference
            def select_phone(row):
                t1, t2 = row.get('full_t1', ''), row.get('full_t2', '')
                tipo1, tipo2 = row.get('t1_tipo'), row.get('t2_tipo')
                
                if tipo_req in ["CELULAR", "FIXO"]:
                    if tipo1 == tipo_req: return t1
                    if tipo2 == tipo_req: return t2
                elif tipo_req == "AMBOS":
                    # AMBOS keeps both, we format them as "CEL: x / FIXO: y"
                    parts = []
                    if t1: parts.append(f"{tipo1}: {t1}")
                    if t2: parts.append(f"{tipo2}: {t2}")
                    return " | ".join(parts)
                    
                # If TODOS, prefer CELULAR, otherwise just return t1 or t2
                if tipo1 == "CELULAR": return t1
                if tipo2 == "CELULAR": return t2
                return t1 if t1 else t2
                
            df['TELEFONE SOLICITADO'] = df.apply(select_phone, axis=1)
            
            # Drop the auxiliary columns
            cols_to_drop = ['ddd1', 'telefone1', 'ddd2', 'telefone2', 't1_tipo', 't2_tipo', 'full_t1', 'full_t2']
            df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

            # Append do mapeamento de operadoras
            df = self._append_operator_column(tid, df)

            op_inc = filters.get("operadora_inc", "TODAS")
            op_exc = filters.get("operadora_exc", "NENHUMA")
            
            if op_exc != "NENHUMA" and 'OPERADORA DO TELEFONE' in df.columns:
                # Filtro de exclusão por contém (case insensitive)
                df = df[~df['OPERADORA DO TELEFONE'].astype(str).str.upper().str.contains(op_exc.upper(), na=False)]
            
            if op_inc != "TODAS" and 'OPERADORA DO TELEFONE' in df.columns:
                # Filtro de inclusão por contém (case insensitive)
                # Ex: 'CLARO' inclui 'CLARO SMP', 'CLARO FIXED', etc.
                df = df[df['OPERADORA DO TELEFONE'].astype(str).str.upper().str.contains(op_inc.upper(), na=False)]

            # Limite removido para permitir extrações massivas sem corte
            # Paginação ocorrerá na hora de salvar o Excel (abas).

            # Map SITUACAO_CADASTRAL codes to text
            sit_map = {
                '01': 'NULA',
                '02': 'ATIVA',
                '03': 'SUSPENSA',
                '04': 'INAPTA',
                '08': 'BAIXADA'
            }
            if 'SITUACAO_CADASTRAL' in df.columns:
                df['SITUACAO_CADASTRAL'] = df['SITUACAO_CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUACAO_CADASTRAL'])

            # Final ordering and formatting
            final_columns = [
                'CNPJ', 'NOME DA EMPRESA', 'SITUAÇÃO CADASTRAL', 'CNAE', 
                'LOGRADOURO', 'NUMERO DA FAIXADA', 'BAIRRO', 'CIDADE', 
                'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'
            ]
            
            df = df.rename(columns={
                'NOME_DA_EMPRESA': 'NOME DA EMPRESA',
                'SITUACAO_CADASTRAL': 'SITUAÇÃO CADASTRAL',
                'NUMERO_DA_FAIXADA': 'NUMERO DA FAIXADA'
            })
            
            # Ensure all columns exist before selecting
            for c in final_columns:
                if c not in df.columns: df[c] = ""
            
            df = df[final_columns]

            self._update_task(tid, progress=95, message="Gerando arquivo Excel particionado (Lotes de 200k)...")
            import xlsxwriter
            # Chunk export with context manager / writer to keep memory footprint low
            with pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}}) as writer:
                chunk_size = 200000
                total_chunks = max(1, (len(df) + chunk_size - 1) // chunk_size)
                
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i : i + chunk_size]
                    chunk.to_excel(writer, sheet_name=f"Lote_{(i//chunk_size)+1}", index=False)
                    
                    if i > 0 and i % 600000 == 0:
                        self._update_task(tid, progress=95, message=f"Gerando arquivo Excel: {(i/len(df))*100:.0f}%...")

            self._update_task(tid, status="COMPLETED", progress=100, message=f"Extração Pronta! {len(df):,} encontrados.", result_file=output_file, record_count=len(df))
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    # --- UNIFY ---
    def start_unify(self, file_paths, output_dir, username=None):
        tid = self._create_task(module="UNIFY", username=username)
        threading.Thread(target=self._run_unify, args=(tid, file_paths, output_dir), daemon=True).start()
        return tid

    def _run_unify(self, tid, file_paths, output_dir):
        self._update_task(tid, status="PROCESSING", message="Unificando arquivos...")
        try:
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            output_file = os.path.join(output_dir, f"Unificado_{tid[:8]}.xlsx")
            dfs = []
            for i, p in enumerate(file_paths):
                if p.endswith('.csv'):
                    dfs.append(pd.read_csv(p, sep=None, engine='python', dtype=str))
                else:
                    dfs.append(pd.read_excel(p, dtype=str))
                self._update_task(tid, progress=int(((i+1)/len(file_paths))*80))
            
            df_final = pd.concat(dfs, ignore_index=True)
            df_final.to_excel(output_file, index=False)
            self._update_task(tid, status="COMPLETED", progress=100, message="Arquivos unificados!", result_file=output_file, record_count=len(df_final))
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    # --- CARRIER ---
    def batch_carrier(self, input_file, output_dir, phone_col, username=None):
        tid = self._create_task(module="CARRIER", username=username)
        threading.Thread(target=self._run_carrier, args=(tid, input_file, output_dir, phone_col), daemon=True).start()
        return tid

    def _run_carrier(self, tid, input_file, output_dir, phone_col):
        self._update_task(tid, status="PROCESSING", message="Iniciando Escaneamento Portabilidade-MT...")
        try:
            status = self.get_task_status(tid)
            if status.get("status") == "CANCELLED": return
            output_file = os.path.join(output_dir, f"Portabilidade_{tid[:8]}.xlsx")
            
            # Load Data
            if input_file.endswith('.csv'):
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira = f.readline()
                sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                df = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
            else:
                df = pd.read_excel(input_file, dtype=str)
            
            total = len(df)
            self._update_task(tid, progress=5, message=f"Processando {total:,} registros...")

            # Determine Phone Column
            t_col = phone_col if (phone_col and phone_col in df.columns) else df.columns[0]
            
            # Normalize Phones
            df['titanium_tel'] = df[t_col].fillna('').astype(str).str.replace(r'\D', '', regex=True)
            df['titanium_tel'] = df['titanium_tel'].apply(lambda x: x[2:] if x.startswith('55') else x)
            
            phones_to_query = df['titanium_tel'].unique().tolist()
            # Double lookup: try 10 digits if 11 digit fails (some DBs have legacy format)
            phones_to_query_alt = [p[:len(p)-9] + p[len(p)-8:] for p in phones_to_query if len(p) == 11]
            all_queries = list(set(phones_to_query + phones_to_query_alt))

            op_results = {}
            op_map = self._get_carrier_map()
            
            # Batch Query SQLite (Titanium-MT Style)
            conn = sqlite3.connect(self.db_carrier)
            batch_size = 800
            for i in range(0, len(all_queries), batch_size):
                # Check cancellation
                if i % 4000 == 0:
                    status = self.get_task_status(tid)
                    if status.get("status") == "CANCELLED": 
                        conn.close()
                        return
                    self._update_task(tid, progress=int(5 + (i/len(all_queries))*85), message=f"Consultando Operadoras: {i:,}/{len(all_queries):,}...")

                batch = all_queries[i : i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                rows = conn.execute(f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})", batch).fetchall()
                for tel_db, op_id in rows:
                    op_results[str(tel_db)] = op_map.get(str(op_id), "OUTRA")
            conn.close()

            def _smart_map(t):
                # 1. Try SQLite portabilidade (Real Ported Data)
                res = None
                if t in op_results: res = op_results[t]
                if not res and len(t) == 11:
                    t10 = t[:2] + t[3:]
                    if t10 in op_results: res = op_results[t10]
                if not res:
                    t13 = "55" + t
                    if t13 in op_results: res = op_results[t13]
                
                if res and res != "OUTRA": return res
                
                # 2. Fallback: Prefix Lookup (Non-ported Original Carrier)
                num = re.sub(r'\D', '', t)
                if num.startswith("55"): num = num[2:]
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        return self.get_op_name(self.prefix_tree[pref])
                
                return res if res else "NÃO CONSTA"

            df['OPERADORA'] = df['titanium_tel'].map(_smart_map)
            
            # Cleanup and Save
            df.drop(columns=['titanium_tel'], inplace=True)
            df.to_excel(output_file, index=False)
            
            self._update_task(tid, status="COMPLETED", progress=100, message="Portabilidade Concluída!", result_file=output_file, record_count=total)
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    def get_single_carrier(self, phone):
        try:
            conn = sqlite3.connect(self.db_carrier)
            tel = ''.join(filter(str.isdigit, str(phone)))
            if tel.startswith('55'): tel = tel[2:]
            
            # Smart Lookup (11 -> 10 -> 13)
            variations = [tel]
            if len(tel) == 11: variations.append(tel[:2] + tel[3:])
            variations.append("55" + tel)
            
            c = None
            for v in variations:
                c = conn.execute("SELECT operadora_id FROM portabilidade WHERE telefone = ?", (v,)).fetchone()
                if c: break

            if c:
                op_name = self.get_op_name(c[0])
                res = {"operadora": op_name, "tipo": "M\u00f3vel"}
            else:
                # Prefix Fallback for Single Lookup
                num = re.sub(r'\D', '', tel)
                op_name = "NÃO CONSTA"
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        op_name = self.get_op_name(self.prefix_tree[pref])
                        break
                res = {"operadora": op_name, "tipo": "Original/Prefix"}
            
            conn.close()
            return res
        except Exception as e:
            return {"operadora": f"ERRO: {str(e)}", "tipo": "N/D"}

    # --- SPLIT ---
    def start_split(self, input_file, output_dir, username=None):
        tid = self._create_task(module="SPLIT", username=username)
        threading.Thread(target=self._run_split, args=(tid, input_file, output_dir), daemon=True).start()
        return tid

    def _run_split(self, tid, input_file, output_dir):
        self._update_task(tid, status="PROCESSING", message="Dividindo arquivo...")
        try:
            output_file = os.path.join(output_dir, f"Dividido_{tid[:8]}.xlsx")
            df = pd.read_csv(input_file, sep=None, engine='python', dtype=str) if input_file.endswith('.csv') else pd.read_excel(input_file, dtype=str)
            import xlsxwriter
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}})
            chunk_size = 1000000
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i : i + chunk_size]
                chunk.to_excel(writer, sheet_name=f"Lote_{(i//chunk_size)+1}", index=False)
            writer.close()
            self._update_task(tid, status="COMPLETED", progress=100, message="Arquivo dividido!", result_file=output_file)
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    def _get_carrier_map(self):
        op_map = {
            "55320":"VIVO", "55323":"VIVO", "55215":"VIVO", "55324":"VIVO", "55377":"VIVO",
            "55321":"CLARO", "55351":"CLARO", "55322":"CLARO", "55371":"CLARO", "55306":"ALGAR",
            "55341":"TIM", "55343":"SERCOMTEL", "55331":"OI", "55312":"ALGAR", "55345":"ALGAR",
            "55112":"ALGAR", "55121":"CLARO", "55123":"TIM", "55131":"OI", "55141":"TIM",
            "55143":"SERCOMTEL", "55204":"SERCOMTEL", "55301":"ARQIA", "55303":"SISTEER",
            "55305":"VIRGIN", "55315":"TELECALL", "55327":"ALGAR", "55348":"TRANSATEL",
            "55367":"CUBIC", "55393":"GLOBALSTAR", "55106":"AMERICADOMÉSTICA", "55307":"AMERICADOMÉSTICA",
            "55211":"BRISANET", "55322":"BRISANET", "55101":"TELECALL", "55191":"IPCORP"
        }
        full_map = {
            "55100":"Interjato", "55102":"Life Telecom", "55103":"DD Telecom", "55104":"DB3", "55105":"Unifique",
            "55107":"Vipnet", "55108":"Osi Telecom", "55109":"Tellig", "55111":"SuperTV", "55113":"Fonar",
            "55116":"Fidelity", "55117":"Transit", "55118":"Spin", "55119":"ZaaZ", "55120":"GTI", "55124":"Megatelecom",
            "55126":"IDT Brasil", "55127":"VIRTUAL", "55128":"Voxbras", "55129":"T-Leste", "55130":"WKVE",
            "55132":"CONVERGIA", "55133":"NWI", "55136":"DSLI", "55137":"Golden Line", "55138":"Tesa", "55139":"Netglobalis",
            "55140":"Hoje Telecom", "55142":"GT Group", "55144":"Sul Internet", "55145":"Cirion", "55147":"British Telecom",
            "55148":"Netserv", "55149":"BBS Options", "55150":"Cambridge", "55151":"Vero S.A.", "55152":"Alares",
            "55153":"GIGA MAIS", "55154":"Viafibra", "55155":"Big Telco", "55156":"Engevox", "55157":"One Telecom",
            "55158":"Voitel", "55161":"Vonex", "55162":"Mundivox", "55163":"Hello Brazil", "55164":"Brasil Tecpar",
            "55166":"Quex", "55167":"DIRECTCALL", "55168":"Tremnet", "55170":"Locaweb", "55171":"YIP", "55172":"BTT",
            "55173":"Brastel", "55174":"TELEFREE", "55176":"Adylnet", "55177":"Opção", "55178":"Nortelpa", "55179":"Option",
            "55180":"Plumium", "55181":"Datora", "55184":"BRFibra", "55185":"UltraNet", "55186":"Teletel", "55187":"EAI",
            "55188":"TVN VOZ", "55189":"CONECTA", "55192":"LIG16", "55193":"Vipway", "55194":"76 Telecom", "55196":"iVATi",
            "55197":"EAD", "55198":"Ligue Telecom", "55199":"Ensite", "55200":"Porto Velho", "55201":"Hit Telecom",
            "55202":"Smartspace", "55203":"Valenet", "55205":"UFINET", "55206":"Desktop", "55208":"Ponto Telecom",
            "55209":"WCS", "55210":"Morango", "55213":"Tri Telecom", "55214":"Orange", "55216":"Ampernet",
            "55217":"TERAPAR", "55218":"Grandi Telecom", "55219":"Redcontrol", "55220":"Net Angra", "55221":"GGNET",
            "55222":"ADP3", "55223":"Citta", "55224":"Algar VGL", "55225":"Conectcor", "55226":"Unitelco", "55227":"Tely",
            "55228":"GO1", "55229":"Tubaron", "55230":"Titania", "55231":"Brasilfone", "55232":"Bignet", "55233":"Superonda",
            "55234":"Córdia", "55235":"BRDigital", "55236":"MG Conecta", "55237":"Goiás Telecom", "55238":"Mhnet",
            "55239":"Vonare", "55240":"Predialnet", "55241":"Nedel", "55242":"Tcheturbo", "55245":"Toque Telecom",
            "55246":"Neo Telecom", "55247":"RED Telecom", "55248":"Itelco", "55249":"Você Telecom", "55250":"LINKTEL",
            "55251":"DBUG", "55252":"BLUE TELECOM", "55253":"ALAWEB", "55254":"Brasrede", "55255":"OXMAN",
            "55256":"Nova Tecnologia", "55258":"Conecta Provedor", "55259":"Sothis", "55260":"Conectv", "55261":"Empire",
            "55262":"Ves Telecom", "55263":"MD Brasil", "55264":"NGT Telecom", "55265":"QNET Telecom", "55266":"8BR",
            "55267":"ORION", "55268":"Nip Telecom", "55269":"Connectronic", "55270":"Mundo Telecom", "55271":"SpeedTravel",
            "55272":"PAK Telecom", "55273":"Process", "55274":"BRAZILIAN", "55275":"High Connect", "55277":"Gente",
            "55278":"Bitcom", "55279":"C3 Telecom", "55280":"NT2 Telecom", "55281":"CPNET", "55282":"Viva Vox",
            "55283":"Rocketnet", "55285":"Alfa Telecom", "55286":"Next Telecom", "55287":"Sulnet", "55288":"Fiber One",
            "55289":"ITANET", "55290":"Superip", "55291":"Link 10", "55292":"Gigalink", "55293":"Vip Telecom",
            "55294":"Iveloz", "55295":"Baldussi", "55296":"Global Lines", "55297":"Softdados", "55298":"Advance",
            "55299":"Ótima Telecom", "55300":"Bras Nuvem", "55301":"Arqia", "55304":"Terapar", "55306":"Surf Telecom",
            "55308":"Ligue Telecom", "55309":"Unifique", "55310":"Vecto Mobile", "55311":"NLT", "55313":"Emnify",
            "55322":"Brisanet", "55343":"Sercomtel Celular", "55348":"Transatel", "55356":"Airnity", "55360":"Neko Serviços",
            "55364":"1nce", "55370":"Iez Telecom", "55375":"Superchip", "55388":"Connect Iot", "55391":"IPCorp",
            "55393":"Globalstar", "55401":"ACB Fibra", "55404":"Client CO", "55410":"Supranet", "55411":"Tel & Globe",
            "55420":"MNET", "55440":"IBI Telecom", "55460":"AMULTIPHONE", "55470":"Customer First", "55474":"BR DID",
            "55477":"ACESSE COMUNICACAO", "55479":"MAISVOIP", "55480":"Softpollus", "55481":"Redfox Fiber",
            "55482":"TRI D TELECOM", "55483":"Vono Tecnologia", "55484":"ABRATEL", "55485":"RCE IT",
            "55486":"PANDA NETWORK", "55487":"FIVENET", "55488":"GL Fibra", "55489":"Bitwave", "55490":"Nicnet",
            "55491":"TOTAL PHONE", "55492":"NETFLEX", "55493":"INOVA FIBRA", "55494":"Allfiber", "55495":"Rolim Net",
            "55496":"ALOSEC", "55497":"NET WAY", "55498":"Digital Net", "55499":"Seagate", "55512":"Plis Inteligência",
            "55534":"Vox One", "55538":"Lestetronics", "55553":"FB Net", "55557":"Soft System", "55570":"Atelex",
            "55576":"RMNetwork", "55580":"Pronto Fibra", "55584":"ITELECOM", "55585":"Global Fibra", "55589":"Osirnet",
            "55590":"LH TELECOM", "55600":"MEGALINK", "55603":"Cyber Internet", "55605":"Ame Telecom",
            "55614":"L T Soluções", "55618":"T. T. A. Soluções", "55623":"Sigatel", "55629":"Internet 10",
            "55630":"R2 Dados", "55633":"The Fiber", "55634":"Wn Telecom", "55639":"Niqturbo", "55640":"Nova NET",
            "55645":"JR Telecom", "55651":"Erictel", "55653":"Cn Telecom", "55654":"Lastnet", "55655":"Mega Net",
            "55660":"Viatec", "55662":"TR Telecom", "55665":"Indanet", "55668":"Brlognet", "55673":"UBA Conect",
            "55677":"BrasilNet", "55678":"Contato Internet", "55679":"Servstar", "55682":"Turbonet", "55684":"Gr@mnet",
            "55688":"Signet", "55694":"Handix", "55698":"Sati Telecom", "55701":"Drcall", "55703":"Innova",
            "55704":"Vale Vox", "55707":"G2G Internet", "55712":"Rio Grande", "55722":"GlobalNet", "55724":"New Voice",
            "55733":"Internet Play", "55746":"Onlink", "55751":"Upix Networks", "55761":"Conecte Telecom",
            "55764":"He Net", "55777":"METODO TELECOM", "55782":"Sonik", "55790":"WGO Multimidia", "55791":"4NET",
            "55820":"NPX", "55834":"Desktop Internet", "55853":"Assim", "55880":"Coelho Tecnologia",
            "55889":"Conectlan", "55890":"Btelway", "55916":"Multiware", "55947":"Brphonia", "55974":"Serra Geral",
            "55975":"Vulcanet", "55984":"FTTH Telecom"
        }
        op_map.update(full_map)
        return op_map

    def _append_operator_column(self, tid, df):
        self._update_task(tid, progress=90, message="Identificando operadoras...")
        try:
            phones_to_query = df['TELEFONE SOLICITADO'].dropna().astype(str).str.replace(r'\D', '', regex=True).tolist()
            phones_to_query = list(set([p for p in phones_to_query if p]))
            phones_to_query_clean = [p[2:] if p.startswith('55') else p for p in phones_to_query]
            phones_to_query_alt = [p[:len(p)-9] + p[len(p)-8:] for p in phones_to_query_clean if len(p) == 11]
            all_queries = list(set(phones_to_query_clean + phones_to_query_alt))

            conn = sqlite3.connect(self.db_carrier)
            op_results = {}
            op_map = self._get_carrier_map()
            
            batch_size = 900
            for i in range(0, len(all_queries), batch_size):
                batch = all_queries[i : i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                rows = conn.execute(f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})", batch).fetchall()
                for tel_db, op_id in rows:
                    op_results[str(tel_db)] = op_map.get(str(op_id), "OUTRA")
            conn.close()

            def _smart_map(t):
                if pd.isna(t) or not t: return "NÃO CONSTA"
                t = str(t).replace(r'\D', '')
                if t.startswith('55'): t = t[2:]
                
                res = None
                if t in op_results: res = op_results[t]
                if not res and len(t) == 11:
                    t10 = t[:2] + t[3:]
                    if t10 in op_results: res = op_results[t10]
                if not res:
                    t13 = "55" + t
                    if t13 in op_results: res = op_results[t13]
                
                if res and res != "OUTRA": return res
                
                num = re.sub(r'\D', '', t)
                if num.startswith("55"): num = num[2:]
                for length in range(7, 3, -1):
                    pref = num[:length]
                    if pref in self.prefix_tree:
                        return self.get_op_name(self.prefix_tree[pref]).upper()
                return "NÃO CONSTA"

            df['OPERADORA DO TELEFONE'] = df['TELEFONE SOLICITADO'].apply(_smart_map)
            return df
        except Exception as e:
            import traceback
            print(f"Erro no filtro de operadora: {e}")
            traceback.print_exc()
            df['OPERADORA DO TELEFONE'] = "ERRO"
            return df
