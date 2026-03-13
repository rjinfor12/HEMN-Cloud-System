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

import clickhouse_connect

class CloudEngine:
    def __init__(self, **kwargs):
        import platform
        if platform.system() == 'Linux':
            self.ch_client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
            self.db_carrier = "/var/www/hemn_cloud/hemn_carrier.db"
        else:
            # Local fallback for development if needed
            self.ch_client = None 
            self.db_carrier = kwargs.get('db_carrier_path')
        self.tasks = {}

    def _create_task(self, module="ENRICH"):
        tid = str(uuid.uuid4())
        self.tasks[tid] = {
            "id": tid,
            "module": module,
            "status": "QUEUED",
            "progress": 0,
            "message": "Aguardando início...",
            "created_at": datetime.now().isoformat()
        }
        return tid

    def _update_task(self, tid, **kwargs):
        if tid in self.tasks:
            self.tasks[tid].update(kwargs)

    def get_task_status(self, tid):
        return self.tasks.get(tid, {"status": "NOT_FOUND"})

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

    def start_enrich(self, input_file, output_dir, name_col, cpf_col):
        tid = self._create_task(module="ENRICH")
        threading.Thread(target=self._run_enrich, args=(tid, input_file, output_dir, name_col, cpf_col), daemon=True).start()
        return tid




    def deep_search(self, name, cpf):
        """Busca rapida unitaria no ClickHouse (Socios + MEIs) com alta assertividade"""
        if not self.ch_client:
            return pd.DataFrame()
        
        basics = []
        name_upper = str(name).strip().upper() if name else None
        cpf_clean = ''.join(filter(str.isdigit, str(cpf or "")))
        cpf_mask = f"***{cpf_clean[3:9]}**" if len(cpf_clean) >= 11 else None
        
        name_frags = name_upper.split() if name_upper else []
        name_pattern = f"%{'%'.join(name_frags)}%" if name_frags else None

        # 1. Stage 1: Exact Name + CPF Mask in SOCIOS
        if name_upper and cpf_mask:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE upper(nome_socio) = %(n)s AND cnpj_cpf_socio = %(c)s LIMIT 50",
                {'n': name_upper, 'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])

        # 2. Stage 2: MEI search in EMPRESAS (often name + CPF in razao_social)
        if name_pattern:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE %(n)s LIMIT 50",
                {'n': name_pattern}
            )
            basics.extend([r[0] for r in res.result_rows])
            
            if cpf_clean and len(cpf_clean) >= 11:
                res = self.ch_client.query(
                    "SELECT DISTINCT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(c)s LIMIT 50",
                    {'c': f"%{cpf_clean}%"}
                )
                basics.extend([r[0] for r in res.result_rows])

        # 3. Stage 3: Broad search in SOCIOS by name pattern
        if name_pattern:
             res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE %(n)s LIMIT 50",
                {'n': name_pattern}
            )
             basics.extend([r[0] for r in res.result_rows])

        # 4. Stage 4: Search by CPF mask only (fallback)
        if cpf_mask and not basics:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = %(c)s LIMIT 50",
                {'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])

        if not basics:
            return pd.DataFrame()
        
        basics = list(set(basics))[:50]
        
        final_query = f"""
            SELECT 
                e.razao_social, 
                multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS cnpj_completo,
                coalesce(s.nome_socio, e.razao_social) as nome_socio, 
                coalesce(s.cnpj_cpf_socio, 'CONSULTAR RAZAO') as cnpj_cpf_socio,
                est.correio_eletronico as email_novo,
                concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', m.descricao, '/', est.uf) as endereco_completo,
                est.ddd1 as ddd_novo,
                est.telefone1 as telefone_novo,
                multiIf(length(est.telefone1) = 9 OR (length(est.telefone1) = 8 AND substring(est.telefone1, 1, 1) IN ('6','7','8','9')), 'CELULAR', 'FIXO') as tipo_telefone
            FROM hemn.estabelecimento est
            JOIN hemn.empresas e ON est.cnpj_basico = e.cnpj_basico
            LEFT JOIN hemn.socios s ON est.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE est.cnpj_basico IN (%(basics)s)
            LIMIT 100
        """
        
        res = self.ch_client.query(final_query, {'basics': basics})
        df = pd.DataFrame(res.result_rows, columns=res.column_names)
        
        if name_upper:
            def is_match(row):
                full_text = f"{str(row['razao_social'])} {str(row['nome_socio'])}".upper()
                matches = sum(1 for frag in name_frags if frag in full_text)
                return matches >= min(2, len(name_frags))

            df = df[df.apply(is_match, axis=1)]
            
        return df.head(50)
    def _run_enrich(self, tid, input_file, output_dir, name_col, cpf_col):
        self._update_task(tid, status="PROCESSING", message="Iniciando Escaneamento Titanium-MT (Motor Paralelo)...")
        try:
            start_time = time.time()
            output_file = os.path.join(output_dir, f"Enriquecido_{tid[:8]}.xlsx")
            
            if input_file.endswith('.csv'):
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira = f.readline()
                sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                df_in = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
            else:
                df_in = pd.read_excel(input_file, dtype=str)
            
            total = len(df_in)
            
            # --- PHASE 0: NORMALIZAÇÃO ---
            if name_col in df_in.columns: n_col = name_col
            else: n_col = df_in.columns[1] if len(df_in.columns) > 1 else df_in.columns[0]
            if cpf_col in df_in.columns: c_col = cpf_col
            else: c_col = df_in.columns[0]
            
            df_in['titanium_nome'] = df_in[n_col].fillna('').astype(str).str.upper().str.strip().apply(remove_accents)
            df_in['titanium_cpf'] = df_in[c_col].fillna('').astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)

            # --- PHASE 1: BATCH PROCESSING (EXTREME SPEED) ---
            # Extract all CPFs and Names
            all_cpfs = df_in['titanium_cpf'].tolist()
            all_names = df_in['titanium_nome'].tolist()
            
            # Identify valid CPFs for bulk lookup
            valid_cpfs = [cpf for cpf in all_cpfs if len(cpf) >= 11]
            valid_masks = [f"***{cpf[3:9]}**" for cpf in valid_cpfs]
            
            # Combine exact CPFs and typical masks for MEI/Socios
            search_terms = list(set(valid_cpfs + valid_masks))
            
            # Prepare Global Cache
            global_cache = {}
            found_count = 0
            
            if search_terms:
                self._update_task(tid, progress=2, message=f"Preparando Extração Paralela ({len(search_terms)} chaves)...")
            if search_terms:
                self._update_task(tid, progress=2, message=f"Preparando Extração Paralela ({len(search_terms)} chaves)...")
                
                # Fetch basic CNPJs for socios
                self._update_task(tid, progress=10, message="Buscando Matrizes via Sócios no ClickHouse...")
                res_socios = self.ch_client.query(
                    "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio IN %(keys)s", 
                    {'keys': search_terms}
                )
                basic_cnpjs = {r[0] for r in res_socios.result_rows}
                
                # Fetch basic CNPJs for empresas (direct CNPJ matches)
                self._update_task(tid, progress=25, message="Buscando Matrizes Diretas no ClickHouse...")
                res_empresas = self.ch_client.query(
                    "SELECT DISTINCT cnpj_basico FROM hemn.empresas WHERE cnpj_basico IN %(keys)s",
                    {'keys': search_terms}
                )
                basic_cnpjs.update([r[0] for r in res_empresas.result_rows])
                
                basic_list = list(basic_cnpjs)
                if basic_list:
                    self._update_task(tid, progress=40, message=f"Extraindo dados de {len(basic_list)} Matrizes...")
                    
                    q = f"""
                    SELECT 
                        s.cnpj_cpf_socio AS cpf_mask,
                        e.razao_social, 
                        estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, 
                        estab.situacao_cadastral, estab.uf, mun.descricao AS municipio_nome, 
                        estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, 
                        estab.correio_eletronico, estab.tipo_logradouro, estab.logradouro, 
                        estab.numero, estab.complemento, estab.bairro, estab.cep, 
                        estab.cnae_fiscal, estab.municipio
                    FROM hemn.estabelecimento estab
                    JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
                    LEFT JOIN hemn.municipio mun ON estab.municipio = mun.codigo
                    LEFT JOIN hemn.socios s ON s.cnpj_basico = estab.cnpj_basico
                    WHERE estab.cnpj_basico IN %(keys)s
                    """
                    res_details = self.ch_client.query(q, {'keys': basic_list})
                    all_details = res_details.result_rows
                    db_cols = res_details.column_names
                    
                    self._update_task(tid, progress=75, message="Filtrando Resultados por Prioridade de Ativação...")
                    
                    for hit in all_details:
                        hit_dict = dict(zip(db_cols, hit))
                        cpf_mask = hit_dict['cpf_mask']
                        if not cpf_mask: cpf_mask = hit_dict['cnpj_basico']
                            
                        situacao = str(hit_dict['situacao_cadastral']).zfill(2)
                        
                        if cpf_mask in global_cache:
                            if global_cache[cpf_mask]['SITUACAO_CODIGO'] == '02' or situacao != '02':
                                continue
                                
                        addr_data = self._parse_address_columns(hit_dict)
                        cont_data = self._parse_contact_columns(hit_dict)
                        mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
                        
                        global_cache[cpf_mask] = {
                            'CNPJ': f"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}",
                            'SITUACAO_CODIGO': situacao,
                            'cnpj_completo': f"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}",
                            'razao_social': hit_dict['razao_social'], 
                            'situacao': mapping.get(situacao, 'ATIVA'),
                            'cnae': hit_dict['cnae_fiscal'], 'logradouro': hit_dict['logradouro'], 'numero': hit_dict['numero'], 'complemento': hit_dict['complemento'],
                            'bairro': hit_dict['bairro'], 'cidade': str(hit_dict['municipio_nome']).upper(), 'uf': hit_dict['uf'], 'cep': hit_dict['cep'],
                            'ddd_novo': hit_dict['ddd1'], 'telefone_novo': hit_dict['telefone1'], 'email_novo': hit_dict['correio_eletronico'],
                            'endereco_completo': f"{hit_dict['logradouro']}, {hit_dict['numero']} - {hit_dict['bairro']} - {hit_dict['municipio_nome']}/{hit_dict['uf']}"
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
                        
                found_count = df_merged['CNPJ'].notna().sum()
                df_final = df_merged.drop(columns=['titanium_cpf', 'titanium_nome', 'mask_calc', 'lookup_key', 'CNPJ', 'SITUACAO_CODIGO'], errors='ignore')
            else:
                found_count = 0
                df_final = df_in.drop(columns=['titanium_cpf', 'titanium_nome'], errors='ignore')

            # Salvar no Excel de forma ultra rapida
            self._update_task(tid, progress=95, message="Salvando arquivo .xlsx resultante...")
            df_final.to_excel(output_file, index=False)
            total_time = time.time() - start_time
            
            # Converter numpy.int64 para int python nativo para evitar erro 500 no FastAPI
            fc_native = int(found_count)
            total_native = int(total)
            
            msg = f"TITANIUM-DONE: V2.0 Processou {total_native} linhas. {fc_native} encontrados em {total_time:.1f}s."
            self._update_task(tid, status="COMPLETED", progress=100, message=msg, result_file=output_file, record_count=fc_native)

        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"TITANIUM-ERROR: {str(e)}")

    # --- EXTRACTION (FULL FILTERS) ---
    def start_extraction(self, filters, output_dir):
        tid = self._create_task(module="EXTRACTION")
        threading.Thread(target=self._run_extraction, args=(tid, filters, output_dir), daemon=True).start()
        return tid

    def _run_extraction(self, tid, filters, output_dir):
        self._update_task(tid, status="PROCESSING", progress=1, message="Iniciando motores ClickHouse...")
        try:
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

            where_clause = " AND ".join(conds) if conds else "1=1"
            
            q = f"""
                SELECT e.razao_social, 
                       concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
                       m.descricao as CIDADE, estab.uf, estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2 
                FROM hemn.estabelecimento estab 
                JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico 
                LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
                WHERE {where_clause} 
                LIMIT 100000
            """
            
            self._update_task(tid, progress=20, message="Executando extração em massa no ClickHouse...")
            res = self.ch_client.query(q, params)
            df = pd.DataFrame(res.result_rows, columns=res.column_names)

            if df.empty:
                self._update_task(tid, status="COMPLETED", progress=100, message="Nenhum registro encontrado.", record_count=0)
                return

            self._update_task(tid, progress=85, message="Filtrando telefones...")
            tipo_req = filters.get("tipo_tel", "TODOS")
            if tipo_req != "TODOS":
                def check_tel(d, t):
                    if not t: return None
                    t = str(t).strip()
                    if len(t) == 9 or (len(t) == 8 and t[0] in '6789'): return "CELULAR"
                    return "FIXO"
                df['t1'] = df.apply(lambda x: check_tel(x['ddd1'], x['telefone1']), axis=1)
                df['t2'] = df.apply(lambda x: check_tel(x['ddd2'], x['telefone2']), axis=1)
                if tipo_req == "AMBOS": 
                    df = df[((df['t1']=="CELULAR") & (df['t2']=="FIXO")) | ((df['t1']=="FIXO") & (df['t2']=="CELULAR"))]
                else: 
                    df = df[(df['t1']==tipo_req) | (df['t2']==tipo_req)]

            df.to_excel(output_file, index=False)
            self._update_task(tid, status="COMPLETED", progress=100, message=f"Extração Pronta! {len(df):,} encontrados.", result_file=output_file, record_count=len(df))
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    # --- CARRIER ---
    def batch_carrier(self, input_file, output_dir, phone_col):
        tid = self._create_task(module="CARRIER")
        threading.Thread(target=self._run_carrier, args=(tid, input_file, output_dir, phone_col), daemon=True).start()
        return tid

    def _run_carrier(self, tid, input_file, output_dir, phone_col):
        self._update_task(tid, status="PROCESSING", message="Consultando Operadoras...")
        try:
            output_file = os.path.join(output_dir, f"Portabilidade_{tid[:8]}.xlsx")
            df = pd.read_csv(input_file, sep=None, engine='python', dtype=str) if input_file.endswith('.csv') else pd.read_excel(input_file, dtype=str)
            conn = sqlite3.connect(self.db_carrier)
            results = []
            total = len(df)
            op_map = {"55320":"VIVO", "55321":"CLARO", "55341":"TIM", "55331":"OI"}
            for i, row in enumerate(df.itertuples(index=False)):
                if i % 500 == 0: self._update_task(tid, progress=int((i/total)*100))
                r = dict(zip(df.columns, row))
                tel = ''.join(filter(str.isdigit, str(r.get(phone_col, ''))))
                if tel.startswith('55'): tel = tel[2:]
                c = conn.execute("SELECT operadora_id FROM portabilidade WHERE telefone = ?", (tel,)).fetchone()
                r['OPERADORA'] = op_map.get(c[0] if c else "", "NÃO CONSTA")
                results.append(r)
            pd.DataFrame(results).to_excel(output_file, index=False)
            conn.close()
            self._update_task(tid, status="COMPLETED", progress=100, message="Concluído!", result_file=output_file)
        except Exception as e:
            self._update_task(tid, status="FAILED", message=f"Erro: {str(e)}")

    # --- SPLIT ---
    def start_split(self, input_file, output_dir):
        tid = self._create_task(module="SPLIT")
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
