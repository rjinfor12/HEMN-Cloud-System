import os
import pandas as pd
import glob
import time
import threading
import sqlite3
import unicodedata
import re
import csv

import sys
def resource_path(relative_path):
    """ Retorna o caminho absoluto do recurso, compatível com PyInstaller --onefile """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

class ConsolidationEngine:
    def __init__(self, target_dir, output_file, columns=None, progress_callback=None, log_callback=None, usage_callback=None):
        self.target_dir = target_dir
        self.output_file = output_file
        self.columns = columns if columns else ['CLIENTE_NOME', 'DOC']
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.usage_callback = usage_callback
        self.is_running = False
        self.stop_requested = False
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        # Cache de Operadoras para Performance Nuclear
        self._carrier_cache = {}

    def consolidate(self):
        """Alias para manter compatibilidade com a GUI."""
        return self.run()

    def _is_valid_phone(self, phone):
        """Hardening total contra notação científica e contatos vazios."""
        if not phone: return False
        s = str(phone).strip().lower()
        if s == '' or s == 'none' or s == 'nan' or 'e+' in s: return False
        digits = "".join(filter(str.isdigit, s))
        if len(digits) < 8 or digits.count('0') == len(digits): return False
        return True

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        print(message)

    def update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def run(self):
        self.is_running = True
        self.stop_requested = False
        try:
            self._process()
        except Exception as e:
            self.log(f"ERRO CRÍTICO: {str(e)}")
        finally:
            self.is_running = False

    def stop(self):
        self.stop_requested = True

    def _process(self):
        start_time = time.time()
        all_files = glob.glob(os.path.join(self.target_dir, "*.xlsx")) + glob.glob(os.path.join(self.target_dir, "*.csv"))
        
        if not all_files:
            self.log("Nenhum arquivo Excel ou CSV encontrado na pasta selecionada.")
            return

        self.log(f"Iniciando consolidação de {len(all_files)} arquivos...")
        
        total_files = len(all_files)
        limite_excel = 1000000
        output_is_excel = self.output_file.endswith('.xlsx')
        
        # Modo Streaming para Unificação (Economia Radical de RAM)
        try:
            if output_is_excel:
                import xlsxwriter
                writer = pd.ExcelWriter(self.output_file, engine='xlsxwriter', engine_kwargs={'options': {'constant_memory': True}})
                current_row = 0
                current_sheet = 1
                sheet_name = f"Parte_{current_sheet}"
            else:
                # Se for CSV, começamos o arquivo limpo
                with open(self.output_file, 'w', encoding='utf-8-sig'): pass

            first_file = True
            total_linhas_processadas = 0

            for i, file_path in enumerate(all_files):
                if self.stop_requested:
                    self.log("Processamento interrompido pelo usuário.")
                    break

                nome_arquivo = os.path.basename(file_path)
                self.log(f"[{i+1}/{total_files}] Lendo {nome_arquivo}...")
                
                try:
                    # Ler em chunks se for CSV para não estourar a RAM se um dos arquivos for gigante
                    if file_path.endswith('.csv'):
                        # Detectar separador
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            primeira = f.readline()
                        sep = ';' if ';' in primeira else ','
                        chunks_read = pd.read_csv(file_path, sep=sep, engine='c', usecols=lambda c: c in self.columns, chunksize=100000, dtype=str)
                    else:
                        # Excel infelizmente não suporta chunksize nativo fácil no pandas read_excel sem estourar RAM do zip, mas lemos o DF inteiro
                        df_full = pd.read_excel(file_path, usecols=lambda c: c in self.columns, dtype=str)
                        chunks_read = [df_full]

                    for df_chunk in chunks_read:
                        df_chunk = df_chunk.dropna(how='all')
                        if df_chunk.empty: continue
                        
                        count_chunk = len(df_chunk)
                        total_linhas_processadas += count_chunk
                        
                        if output_is_excel:
                            # Gerenciamento de abas para limite de 1M
                            if current_row + count_chunk > limite_excel:
                                # Se o chunk atual estoura a aba, escrevemos o que cabe e criamos nova aba (simplificado: cria nova aba se chegar perto)
                                current_sheet += 1
                                current_row = 0
                                sheet_name = f"Parte_{current_sheet}"
                                self.log(f"  -> Criando nova aba: {sheet_name}")
                            
                            df_chunk.to_excel(writer, sheet_name=sheet_name, index=False, startrow=current_row, header=(current_row == 0))
                            current_row += count_chunk
                        else:
                            # Append direto no CSV
                            df_chunk.to_csv(self.output_file, mode='a', index=False, sep=';', encoding='utf-8-sig', header=first_file)
                            first_file = False

                    self.update_progress(i + 1, total_files)
                except Exception as e:
                    self.log(f"  Erro ao processar {nome_arquivo}: {e}")

            if output_is_excel:
                writer.close()

            self.log(f"Sucesso! Total de {total_linhas_processadas} linhas consolidadas em: {self.output_file}")
            self.log(f"Tempo total: {time.time() - start_time:.2f} segundos.")

        except Exception as e:
            self.log(f"ERRO NA CONSOLIDAÇÃO: {str(e)}")

    def optimize_database(self, db_path):
        """Cria índices estruturais para performance máxima em bases gigantes."""
        try:
            start_time = time.time()
            self.log(">>> INICIANDO OTIMIZAÇÃO ESTRUTURAL (TUNA PERFORMANCE) <<<")
            self.log("Isso pode levar alguns minutos, por favor aguarde...")
            
            conn = sqlite3.connect(db_path, timeout=60.0)
            cursor = conn.cursor()
            
            # 1. Ajustar configurações de escrita rápida
            cursor.execute("PRAGMA journal_mode = OFF")
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA cache_size = 1000000") # 1GB cache temp
            
            indexes = [
                ("idx_estab_municipio", "estabelecimento(municipio)"),
                ("idx_estab_uf", "estabelecimento(uf)"),
                ("idx_estab_situacao", "estabelecimento(situacao_cadastral)"),
                ("idx_estab_cnae", "estabelecimento(cnae_fiscal)"),
                ("idx_municipio_codigo", "municipio(codigo)"),
                ("idx_cnae_codigo", "cnae(codigo)")
            ]
            
            for i, (name, target) in enumerate(indexes):
                if self.stop_requested: break
                self.log(f"[{i+1}/{len(indexes)}] Criando índice em {target}...")
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {target}")
                conn.commit()
            
            self.log("Executando ANALYZE para otimizar o planejador de queries...")
            cursor.execute("ANALYZE")
            conn.commit()
            
            conn.close()
            self.log(f"SUCESSO: Base de dados otimizada em {time.time() - start_time:.2f}s!")
            return True
        except Exception as e:
            self.log(f"ERRO NA OTIMIZAÇÃO: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                try: conn.close()
                except: pass


    def _format_address_row(self, row):
        """Formata o endereço completo a partir de uma linha de resultado (Para GUI)."""
        # Suporta tanto Series do pandas quanto dicionários
        def g(field): return row.get(field) if hasattr(row, 'get') else row[field]
        
        addr = f"{g('tipo_logradouro') or ''} {g('logradouro') or ''}, {g('numero') or ''}"
        complemento = g('complemento')
        if complemento and str(complemento) != 'None':
            addr += f" - {complemento}"
        
        cidade = g('municipio_nome') or g('municipio') or ''
        addr += f" | {g('bairro') or ''} | {cidade}-{g('uf') or ''} | CEP: {g('cep') or ''}"
        return addr.strip().replace("  ", " ")

    def _parse_address_columns(self, row):
        """Avalia e separa o endereço em colunas válidas."""
        def g(field): 
            v = row.get(field) if hasattr(row, 'get') else row[field]
            return str(v or '').strip() if str(v) != 'None' else ''
            
        tipo_log = g('tipo_logradouro')
        log_raw = g('logradouro')
        logradouro = f"{tipo_log} {log_raw}".strip()
        numero = g('numero')
        complemento = g('complemento')
        bairro = g('bairro')
        municipio = g('municipio_nome') or g('municipio')
        uf = g('uf')
        cep = g('cep')
        
        return pd.Series([logradouro, numero, complemento, bairro, municipio, uf, cep])

    def _parse_contact_columns(self, row, tipo_filtro="TODOS"):
        """Avalia e separa o contato em colunas, checando telefone 1 e 2."""
        def g(field): return row.get(field) if hasattr(row, 'get') else row[field]
        
        email = str(g('correio_eletronico') or '').strip()
        if email.lower() == 'none' or not email: email = ''
        
        def analisar_telefone(d, t):
            ddd_cl = ''.join(filter(str.isdigit, str(d or '')))
            tel_cl = ''.join(filter(str.isdigit, str(t or '')))
            
            # Normalização para 9 dígitos (Móvel BR) ou 8 dígitos (Fixo)
            if len(tel_cl) == 8:
                if tel_cl.startswith(('6', '7', '8', '9')):
                    return ddd_cl, '9' + tel_cl, "CELULAR"
                return ddd_cl, tel_cl, "FIXO"
            
            if len(tel_cl) == 9:
                return ddd_cl, tel_cl, "CELULAR"
            
            return "", "", ""

        ddd1, tel1, tipo1 = analisar_telefone(g('ddd1'), g('telefone1'))
        ddd2, tel2, tipo2 = analisar_telefone(g('ddd2'), g('telefone2'))
        
        best_ddd, best_tel, best_tipo = "", "", ""
        
        if tipo_filtro in ["TODOS", "AMBOS"] or not tipo_filtro:
            # Traz o primeiro válido
            if tel1: best_ddd, best_tel, best_tipo = ddd1, tel1, tipo1
            elif tel2: best_ddd, best_tel, best_tipo = ddd2, tel2, tipo2
        else:
            # Prioriza a opção que bate com o filtro
            if tipo1 == tipo_filtro: best_ddd, best_tel, best_tipo = ddd1, tel1, tipo1
            elif tipo2 == tipo_filtro: best_ddd, best_tel, best_tipo = ddd2, tel2, tipo2
            elif tel1: best_ddd, best_tel, best_tipo = ddd1, tel1, tipo1 # Fallback para o primeiro
            elif tel2: best_ddd, best_tel, best_tipo = ddd2, tel2, tipo2 # Fallback
            
        return pd.Series([best_ddd, best_tel, best_tipo, email])

    def search_cnpj_by_name_cpf(self, db_path, name, cpf_digits="", only_with_phone=False):
        """Busca CNPJs vinculados a um nome e/ou CPF."""
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            self.log(f"Conectado ao banco: {os.path.basename(db_path)}")
            
            # Sanitização e normalização (Remover acentos)
            name = remove_accents(name.upper().strip())
            # Busca Elástica: Substitui espaços por curingas para capturar variações
            name_query = f"%{name.replace(' ', '%')}%"
            
            self.log(f"Iniciando busca SQL para: {name} (Elastic: {name_query})")
            
            # Gerar nome base (sem JUNIOR, FILHO, etc) para busca mais ampla
            suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR']
            base_name = name
            for sfx in suffixes:
                if base_name.endswith(sfx):
                    base_name = base_name[:-len(sfx)].strip()
                    break
            
            # Filtro de CPF
            cpf_filter_socios = ""
            if cpf_digits:
                cpf_digits = ''.join(filter(str.isdigit, str(cpf_digits)))
                if len(cpf_digits) >= 6:
                    cpf_miolo = cpf_digits if len(cpf_digits) == 6 else cpf_digits[3:9]
                    cpf_filter_socios = f"AND (s.cnpj_cpf_socio LIKE '%{cpf_miolo}%' OR s.cnpj_cpf_socio = '{cpf_digits}')"

            # ESTRATÉGIA DE ALTA PERFORMANCE (V16 - CUMULATIVE & ROBUST):
            # 1. Tenta CPF/Máscara (Instantâneo)
            # 2. Busca por Nome em Sócios (FTS-like: Prefixo + Elástico)
            # 3. Busca em Empresas (MEI / Doc Fallback)
            # 4. Acumula tudo
            
            def safe_log(m):
                self.log(m)

            def validate_match(row_name, row_cpf):
                if not row_name: return False
                r_name = remove_accents(str(row_name).upper().strip())
                
                # Se o CPF for idêntico, confiamos 100%
                if cpf_digits and str(row_cpf) == cpf_digits:
                    return True
                
                # Normalização de nomes (Remover dígitos do fim - comum em MEI)
                r_name_clean = re.sub(r'\d+$', '', r_name).strip()
                
                # Normalização de nomes (Remover sufixos para comparar base)
                r_name_base = r_name_clean
                for sfx in [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR']:
                    if r_name_base.endswith(sfx):
                        r_name_base = r_name_base[:-len(sfx)].strip()
                        break
                
                # O nome base deve bater
                if base_name not in r_name_base and r_name_base not in base_name:
                    return False
                
                # Se o usuário especificou um sufixo, o resultado também deve ter um sufixo
                suffixes_list = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR']
                search_has_suffix = any(name.endswith(sfx) for sfx in suffixes_list)
                result_has_suffix = any(r_name_clean.endswith(sfx) for sfx in suffixes_list)
                
                if search_has_suffix and not result_has_suffix:
                    return False # Buscou Junior, não queremos o Pai
                
                return True

            all_results = []
            
            # --- FASE 1: Busca por Documento (SOCIOS) ---
            if cpf_digits:
                mask = f"***{cpf_digits[3:9]}**" if len(cpf_digits) == 11 else None
                safe_log(f"Phase 1: Buscando CPF/Mask em Sócios...")
                query_doc = """
                SELECT 
                    s.cnpj_basico, e.razao_social, s.nome_socio, s.cnpj_cpf_socio,
                    estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral,
                    estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2,
                    estab.correio_eletronico, estab.uf, m.descricao AS municipio_nome,
                    estab.tipo_logradouro, estab.logradouro, estab.numero,
                    estab.complemento, estab.bairro, estab.cep, estab.cnae_fiscal,
                    estab.municipio, estab.cnpj as cnpj_completo_db
                FROM socios s
                LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
                LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE s.cnpj_cpf_socio = ? OR s.cnpj_cpf_socio = ?
                LIMIT 100
                """
                df_temp = pd.read_sql_query(query_doc, conn, params=[cpf_digits, mask])
                if not df_temp.empty:
                    df_temp['is_valid'] = df_temp.apply(lambda x: validate_match(x['nome_socio'], x['cnpj_cpf_socio']), axis=1)
                    valid = df_temp[df_temp['is_valid']].drop(columns=['is_valid'])
                    if not valid.empty: all_results.append(valid)

            # --- FASE 2: Busca por Nome (SOCIOS) ---
            if name and len(name) > 3:
                safe_log(f"Phase 2: Buscando Nome em Sócios...")
                query_socios = """
                SELECT 
                    s.cnpj_basico, e.razao_social, s.nome_socio, s.cnpj_cpf_socio,
                    estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral,
                    estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2,
                    estab.correio_eletronico, estab.uf, m.descricao AS municipio_nome,
                    estab.tipo_logradouro, estab.logradouro, estab.numero,
                    estab.complemento, estab.bairro, estab.cep, estab.cnae_fiscal,
                    estab.municipio, estab.cnpj as cnpj_completo_db
                FROM socios s
                LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
                LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE s.nome_socio LIKE ? OR s.nome_socio LIKE ?
                LIMIT 100
                """
                # Tenta prefixo E elástico juntos para garantir cobertura total
                df_socios = pd.read_sql_query(query_socios, conn, params=[f"{name}%", name_query])
                if not df_socios.empty:
                    df_socios['is_valid'] = df_socios.apply(lambda x: validate_match(x['nome_socio'], x['cnpj_cpf_socio']), axis=1)
                    valid = df_socios[df_socios['is_valid']].drop(columns=['is_valid'])
                    if not valid.empty: all_results.append(valid)

            # --- FASE 3: Busca Fallback (EMPRESAS / MEI) ---
            if name and len(name) > 3:
                safe_log(f"Phase 3: Buscando Fallback em Empresas...")
                query_mei = """
                SELECT 
                    e.cnpj_basico, e.razao_social, e.razao_social AS nome_socio,
                    'N/A' AS nome_representante, 'N/A' AS cnpj_cpf_socio,
                    estab.cnpj_ordem, estab.cnpj_dv, estab.situacao_cadastral,
                    estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2,
                    estab.correio_eletronico, estab.uf, m.descricao AS municipio_nome,
                    estab.tipo_logradouro, estab.logradouro, estab.numero,
                    estab.complemento, estab.bairro, estab.cep, estab.cnae_fiscal,
                    estab.municipio, estab.cnpj as cnpj_completo_db
                FROM empresas e
                LEFT JOIN estabelecimento estab ON e.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE e.razao_social LIKE ? OR e.razao_social LIKE ? OR e.razao_social LIKE ?
                LIMIT 100
                """
                params = [f"{name}%", name_query, f"%{cpf_digits}%"] if cpf_digits else [f"{name}%", name_query, name_query]
                df_mei = pd.read_sql_query(query_mei, conn, params=params)
                if not df_mei.empty:
                    df_mei['is_valid'] = df_mei.apply(lambda x: validate_match(x['nome_socio'], x['cnpj_cpf_socio']), axis=1)
                    valid = df_mei[df_mei['is_valid']].drop(columns=['is_valid'])
                    if not valid.empty: all_results.append(valid)

            # --- CONSOLIDACAO ---
            if not all_results:
                safe_log(f"Nenhum registro compatível encontrado.")
                conn.close()
                return pd.DataFrame()
            
            df = pd.concat(all_results).drop_duplicates(subset=['cnpj_basico', 'cnpj_ordem', 'cnpj_dv'])

            # Formata o CNPJ e Situação
            mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
            df['situacao'] = df['situacao_cadastral'].map(mapping).fillna('DESCONHECIDA')
            df['cnpj_completo'] = df['cnpj_completo_db'].fillna('')
            # Se vier vazio do DB, gera na mão
            mask = df['cnpj_completo'] == ''
            if mask.any():
                df.loc[mask, 'cnpj_completo'] = df.loc[mask].apply(lambda x: f"{x['cnpj_basico']}{x['cnpj_ordem']}{x['cnpj_dv']}", axis=1)
            
            df['endereco_completo'] = df.apply(self._format_address_row, axis=1)
            df[['logradouro', 'numero', 'complemento', 'bairro', 'municipio', 'uf_end', 'cep']] = df.apply(self._parse_address_columns, axis=1, result_type='expand')
            df[['ddd_novo', 'telefone_novo', 'tipo_telefone', 'email_novo']] = df.apply(self._parse_contact_columns, axis=1, result_type='expand')
            
            if only_with_phone:
                df['IS_VAL'] = df['telefone_novo'].apply(self._is_valid_phone)
                df = df[df['IS_VAL'] == True].drop(columns=['IS_VAL'])

            conn.close()
            return df
            
        except Exception as e:
            self.log(f"ERRO CRÍTICO NA ENGINE DE BUSCA: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return None

    def search_cnpj_batch(self, db_path, input_file, name_col, cpf_col, output_file, only_with_phone=False, limit=None):
        """Busca CNPJs para uma lista de nomes e CPFs em uma planilha."""
        try:
            start_time = time.time()
            self.log(f"Lendo arquivo de entrada: {os.path.basename(input_file)}")
            
            if input_file.endswith('.csv'):
                # Detect separator
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    primeira = f.readline()
                sep = ';' if ';' in primeira else (',' if ',' in primeira else '\t')
                
                # Check if we should use column names or fixed indices
                if name_col and cpf_col:
                    df_input = pd.read_csv(input_file, sep=sep, engine='python', dtype=str)
                else:
                    df_input = pd.read_csv(input_file, sep=sep, engine='python', header=None, dtype=str)
            else:
                self.log("Lendo arquivo Excel...")
                if name_col and cpf_col:
                    df_input = pd.read_excel(input_file, dtype=str)
                else:
                    df_input = pd.read_excel(input_file, header=None, dtype=str)
            
            total_nomes = len(df_input)
            self.log(f"Total de registros para processar: {total_nomes}")
            
            # Verifica se precisa forçar CSV por limite do Excel (1M linhas)
            if total_nomes > 1000000 and output_file.endswith('.xlsx'):
                self.log("Volume excede limite do Excel. Forçando exportação para .csv")
                output_file = output_file.replace('.xlsx', '.csv')
            
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            results = []
            
            # Consultas Base (Otimizadas para não recriar a string SQL no Python a cada ciclo)
            base_select = """
                SELECT 
                    e.razao_social, s.cnpj_basico, s.cnpj_cpf_socio, s.nome_socio, estab.cnpj_ordem, estab.cnpj_dv,
                    estab.situacao_cadastral, estab.uf, m.descricao AS municipio_nome,
                    estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, estab.correio_eletronico,
                    estab.tipo_logradouro, estab.logradouro, estab.numero, estab.complemento, estab.bairro,
                    estab.cep, estab.cnae_fiscal, estab.municipio
            """
            q_socios_cpf = base_select + """
                FROM socios s
                LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
                LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE (s.cnpj_cpf_socio = ? OR s.cnpj_cpf_socio = ?) AND (s.nome_socio LIKE ? OR s.nome_representante LIKE ?)
            """
            q_socios_nome = base_select + """
                FROM socios s
                LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
                LEFT JOIN estabelecimento estab ON s.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE (s.nome_socio = ? OR s.nome_representante = ?)
            """
            
            q_mei_cpf = """
                SELECT 
                    e.razao_social, e.cnpj_basico, 'N/A' as cnpj_cpf_socio, e.razao_social as nome_socio, estab.cnpj_ordem, estab.cnpj_dv,
                    estab.situacao_cadastral, estab.uf, m.descricao AS municipio_nome,
                    estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, estab.correio_eletronico,
                    estab.tipo_logradouro, estab.logradouro, estab.numero, estab.complemento, estab.bairro,
                    estab.cep, estab.cnae_fiscal, estab.municipio
                FROM empresas e
                LEFT JOIN estabelecimento estab ON e.cnpj_basico = estab.cnpj_basico
                LEFT JOIN municipio m ON TRIM(estab.municipio) = TRIM(m.codigo)
                WHERE e.razao_social >= ? AND e.razao_social <= ?
                LIMIT 20
            """
            
            cols = ['razao_social', 'cnpj_basico', 'cnpj_cpf_socio', 'nome_socio', 'cnpj_ordem', 'cnpj_dv', 'situacao_cadastral', 'uf', 'municipio_nome', 'ddd1', 'telefone1', 'ddd2', 'telefone2', 'correio_eletronico', 'tipo_logradouro', 'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'cnae_fiscal', 'municipio']
            mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
            suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR']
            csv_header_written = False

            # Limitação de processamento visual para não engasgar fila principal
            for i, row in enumerate(df_input.itertuples(index=False)):
                if self.stop_requested:
                    self.log("Processamento interrompido.")
                    break
                
                # Resolvendo nomes das colunas ou índices
                if name_col and cpf_col:
                    row_dict = dict(zip(df_input.columns, row))
                    nome_raw = row_dict.get(name_col)
                    cpf_raw = row_dict.get(cpf_col)
                else:
                    # Coluna A = 0 (CPF), Coluna B = 1 (NOME)
                    try:
                        cpf_raw = row[0]
                        nome_raw = row[1]
                    except IndexError:
                        continue # Linha inválida

                # Pular cabeçalho se houver
                if i == 0 and (str(cpf_raw).upper().strip() == 'CPF' or str(nome_raw).upper().strip() == 'NOME'):
                    continue

                if pd.isna(nome_raw) or str(nome_raw).strip() == '':
                    continue
                
                nome = remove_accents(str(nome_raw).upper().strip())
                base_nome = nome
                for sfx in suffixes:
                    if base_nome.endswith(sfx):
                        base_nome = base_nome[:-len(sfx)].strip()
                        break

                if i < 3:
                     self.log(f"TITANIUM-DIAG: Processando [{str(cpf_raw)[:4]}...] {nome[:15]}...")

                has_cpf = False
                params_socios = []
                params_mei = []
                
                if pd.notnull(cpf_raw):
                    cpf_digits = ''.join(filter(str.isdigit, str(cpf_raw)))
                    # Pad CPF to 11 digits (handle lost leading zeros)
                    if len(cpf_digits) > 0 and len(cpf_digits) < 11:
                        cpf_digits = cpf_digits.zfill(11)
                        
                    if len(cpf_digits) >= 6:
                        has_cpf = True
                        cpf_miolo = cpf_digits if len(cpf_digits) == 6 else cpf_digits[3:9]
                        cpf_mask = f"***{cpf_miolo}**"
                        
                        nome_like = f"%{base_nome}%"
                        params_socios = [cpf_mask, cpf_digits, nome_like, nome_like] # OPA: Notei que q_socios_cpf usa 4 placeholders
                        params_mei = [f"{nome} {cpf_digits}", f"{nome} {cpf_digits}z"]

                if not has_cpf:
                    params_socios = [f"%{base_nome}%", f"%{base_nome}%"] # Para q_socios_nome
                    params_mei = [f"{nome} ", f"{nome}z"]

                # Limitação de processamento visual para não engasgar fila principal
                if i % 500 == 0:
                    self.update_progress(i + 1, total_nomes)
                if i % 10000 == 0 and i > 0:
                    self.log(f"  -> Já processamos {i} de {total_nomes} clientes. Velocidade Máxima.")
                
                # Executa Queries Nativas C-Level (Otimizado)
                if has_cpf:
                    cursor.execute(q_socios_cpf, params_socios)
                else:
                    cursor.execute(q_socios_nome, params_socios)
                rows_socios = cursor.fetchall()

                cursor.execute(q_mei_cpf, params_mei)
                rows_mei = cursor.fetchall()
                
                all_raw_rows = rows_socios + rows_mei
                
                # Processamento local de Resultados Unicos (Substitui DataFrames.drop_duplicates)
                seen_cnpjs = set()
                valid_found = []
                
                if all_raw_rows:
                    actual_cpf = ''
                    if cpf_col and cpf_col in row_dict and pd.notnull(row_dict[cpf_col]):
                        actual_cpf = ''.join(filter(str.isdigit, str(row_dict[cpf_col])))
                    
                    for r in all_raw_rows:
                        c_basico = r[1]
                        if c_basico in seen_cnpjs: continue
                        
                        r_dict = dict(zip(cols, r))
                        r_name = remove_accents(str(r_dict['nome_socio']).upper())
                        r_cpf = str(r_dict['cnpj_cpf_socio'])
                        
                        is_valid = False
                        if actual_cpf and r_cpf == actual_cpf:
                            is_valid = True
                        else:
                            sfx_match = True
                            for sfx in suffixes:
                                if (sfx in nome) != (sfx in r_name):
                                    sfx_match = False
                                    break
                            if sfx_match and base_nome in r_name:
                                is_valid = True
                                
                        if is_valid:
                            seen_cnpjs.add(c_basico)
                            valid_found.append(r_dict)

                if valid_found:
                    # Vetorização local para o chunk de resultados encontrados para UM cliente
                    df_v = pd.DataFrame(valid_found)
                    df_v['CNPJ'] = df_v['cnpj_basico'] + df_v['cnpj_ordem'] + df_v['cnpj_dv']
                    df_v['SITUACAO'] = df_v['situacao_cadastral'].map(mapping).fillna('DESCONHECIDA')
                    
                    # Filtro estrito: Apenas ATIVA
                    df_v = df_v[df_v['SITUACAO'] == 'ATIVA']
                    
                    if not df_v.empty:
                        # Parsing vetorizado de endereços
                        tipo_log = df_v['tipo_logradouro'].fillna('').astype(str).str.strip()
                        log_raw = df_v['logradouro'].fillna('').astype(str).str.strip()
                        df_v['LOGRADOURO_F'] = (tipo_log + ' ' + log_raw).str.strip()
                        df_v['NUMERO_F'] = df_v['numero'].fillna('').astype(str).str.strip()
                        df_v['COMPLEMENTO_F'] = df_v['complemento'].fillna('').astype(str).str.strip()
                        df_v['BAIRRO_F'] = df_v['bairro'].fillna('').astype(str).str.strip()
                        df_v['CIDADE_F'] = df_v['municipio_nome'].fillna('').astype(str).str.strip()
                        df_v['UF_F'] = df_v['uf'].fillna('').astype(str).str.strip()
                        df_v['CEP_F'] = df_v['cep'].fillna('').astype(str).str.strip()
                        
                        # Parsing vetorizado de contatos
                        def clean_tel(s): return s.fillna('').astype(str).str.replace(r'\D', '', regex=True)
                        d1, t1 = clean_tel(df_v['ddd1']), clean_tel(df_v['telefone1'])
                        d2, t2 = clean_tel(df_v['ddd2']), clean_tel(df_v['telefone2'])
                        
                        # Lógica simplificada vetorizada
                        is_fix1 = t1.str.len() == 8
                        is_cel1 = (t1.str.len() == 9) | (is_fix1 & t1.str.startswith(('6','7','8','9')))
                        
                        df_v['TEL_F'] = t1
                        df_v.loc[is_cel1 & (t1.str.len() == 8), 'TEL_F'] = '9' + t1
                        df_v['DDD_F'] = d1
                        df_v['TIPO_F'] = "FIXO"
                        df_v.loc[is_cel1, 'TIPO_F'] = "CELULAR"
                        
                        # Fallback se tel1 for vazio
                        vazio1 = df_v['TEL_F'] == ''
                        if vazio1.any():
                            # Mesma lógica para tel2 nos vazios
                            pass # Simplificado por hora
                        
                        df_v['EMAIL_F'] = df_v['correio_eletronico'].fillna('').astype(str).str.strip().str.lower()

                        for v_row in df_v.itertuples(index=False):
                            combined = row_dict.copy()
                            combined.update({
                                'CNPJ': v_row.CNPJ,
                                'RAZAO_SOCIAL': v_row.razao_social,
                                'SITUACAO': v_row.SITUACAO,
                                'CNAE': v_row.cnae_fiscal,
                                'LOGRADOURO': v_row.LOGRADOURO_F, 'NUMERO': v_row.NUMERO_F,
                                'COMPLEMENTO': v_row.COMPLEMENTO_F, 'BAIRRO': v_row.BAIRRO_F,
                                'CIDADE': v_row.CIDADE_F, 'UF_END': v_row.UF_F, 'CEP': v_row.CEP_F,
                                'DDD': v_row.DDD_F, 'TELEFONE': v_row.TEL_F,
                                'TIPO': v_row.TIPO_F, 'EMAIL': v_row.EMAIL_F
                            })
                            
                            if only_with_phone:
                                if self._is_valid_phone(combined['TELEFONE']):
                                    results.append(combined)
                            else:
                                results.append(combined)
                        
                # Memory Throttling (Streaming Mode) - Salva RAM jogando blocos no disco a cada 50k
                if len(results) >= 50000:
                    df_chunk = pd.DataFrame(results)
                    if output_file.endswith('.csv'):
                        df_chunk.to_csv(output_file, mode='a', index=False, sep=';', encoding='utf-8-sig', header=not csv_header_written)
                        csv_header_written = True
                    results = []

            conn.close()
            
            # Export Final Chunk
            if results or not csv_header_written:
                df_final = pd.DataFrame(results)
                
                if output_file.endswith('.xlsx'):
                    df_final.to_excel(output_file, index=False)
                else:
                    df_final.to_csv(output_file, mode='a', index=False, sep=';', encoding='utf-8-sig', header=not csv_header_written)
            
            self.log(f"Sucesso! Resultado salvo em: {output_file}")
            self.log(f"Tempo total: {time.time() - start_time:.2f} segundos.")
            
        except Exception as e:
            self.log(f"Erro no processamento em lote: {str(e)}")
    def extract_by_filter(self, db_path, output_file, filters_dict, limit=None):
        """Extrai dados da base por múltiplos filtros simultâneos (Cidade, UF, CNAE, Situação)."""
        try:
            start_time = time.time()
            active_filters = [f"{k}={v}" for k, v in filters_dict.items() if v]
            somente_tel = filters_dict.get("SOMENTE_COM_TELEFONE", False)
            self.log(f"Iniciando extração multifiltro: {', '.join(active_filters)}")
            self.log(f"  -> Filtro Nuclear (Apenas com Telefone): {'ATIVO' if somente_tel else 'INATIVO'}")
            
            conn = sqlite3.connect(db_path, timeout=30.0)
            
            # --- INTEGRAÇÃO EXCEL (CEP + Número) ---
            has_excel_filter = False
            excel_path = filters_dict.get("EXCEL_CEP")
            if excel_path and os.path.exists(excel_path):
                self.log(f"Lendo planilha de CEPs: {excel_path}")
                try:
                    if excel_path.endswith('.csv'):
                        df_cep = pd.read_csv(excel_path, dtype=str)
                    else:
                        df_cep = pd.read_excel(excel_path, dtype=str)
                        
                    if len(df_cep.columns) < 2:
                        self.log(f"ERRO: A planilha precisa ter pelo menos 2 colunas (Coluna A de CEP e Coluna B de Número). Encontramos apenas {len(df_cep.columns)}.")
                        conn.close()
                        return False
                        
                    col_cep = df_cep.columns[0]
                    col_num = df_cep.columns[1]
                    
                    # Limpeza Extrema: Remoção de float ghost (.0) de números lidos como double e zfill(8) para recuperar '0' de CEPs de SPapagados pelo Excel
                    df_cep[col_cep] = df_cep[col_cep].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '', regex=True).str.zfill(8)
                    df_cep[col_num] = df_cep[col_num].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_cep = df_cep[df_cep[col_cep] != '00000000']
                    
                    # PREVENÇÃO DE DUPLICATAS: Remove duplicatas da planilha para não multiplicar os joins
                    df_cep = df_cep.drop_duplicates(subset=[col_cep, col_num])
                    
                    self.log(f"Inserindo {len(df_cep)} localidades na Memória Temporária do Banco...")
                    conn.execute("CREATE TEMPORARY TABLE temp_cep_filter (cep TEXT, numero TEXT)")
                    
                    # Usa executemany em vez de pandas to_sql para evitar table locking e scans no sqlite_master
                    data_tuples = df_cep[[col_cep, col_num]].values.tolist()
                    conn.executemany("INSERT INTO temp_cep_filter (cep, numero) VALUES (?, ?)", data_tuples)
                    
                    conn.execute("CREATE INDEX idx_temp_cep ON temp_cep_filter(cep, numero)")
                    conn.commit()
                    has_excel_filter = True
                except Exception as e:
                    self.log(f"Erro ao ler/processar a planilha de CEPs: {e}")
                    conn.close()
                    return False
            
            # Construção dinâmica do WHERE - TOTALMENTE PARAMETRIZADO (v1.1.6)
            conditions = []
            main_params = []
            
            if filters_dict.get("CIDADE"):
                val = str(filters_dict["CIDADE"]).upper().strip()
                conditions.append("(m.descricao LIKE ? OR estab.municipio = ?)")
                main_params.extend([f"%{val}%", val])
            
            if filters_dict.get("UF"):
                val = str(filters_dict["UF"]).upper().strip()
                conditions.append("estab.uf = ?")
                main_params.append(val)
            
            if filters_dict.get("CNAE"):
                cnae_input = str(filters_dict["CNAE"]).replace(';', ',')
                cnae_list = [c.strip() for c in cnae_input.split(',') if c.strip()][:5]
                if cnae_list:
                    cnae_subparts = []
                    for c in cnae_list:
                        cnae_subparts.append("(estab.cnae_fiscal LIKE ? OR cn.descricao LIKE ?)")
                        main_params.extend([f"%{c}%", f"%{c}%"])
                    conditions.append(f"({' OR '.join(cnae_subparts)})")
            
            if filters_dict.get("SITUAÇÃO"):
                s_map = {'ATIVA': '02', 'BAIXADA': '08', 'SUSPENSA': '03', 'INAPTA': '04', 'NULA': '01'}
                val = str(filters_dict["SITUAÇÃO"]).upper().strip()
                code = s_map.get(val, val)
                conditions.append("estab.situacao_cadastral = ?")
                main_params.append(code)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            if has_excel_filter:
                join_excel = "INNER JOIN temp_cep_filter tcf ON estab.cep = tcf.cep AND estab.numero = tcf.numero"
            else:
                join_excel = ""
                
            # 1. Contagem prévia OTIMIZADA (Busca códigos primeiro para usar índices)
            self.log("Calculando volume de dados da extração...")
            
            # Decomposição do JOIN para performance máxima
            municipio_codes = []
            if filters_dict.get("CIDADE"):
                val = str(filters_dict["CIDADE"]).upper().strip()
                cur = conn.cursor()
                cur.execute("SELECT codigo FROM municipio WHERE descricao LIKE ? OR codigo = ?", (f"%{val}%", val))
                municipio_codes = [r[0] for r in cur.fetchall()]
                if not municipio_codes:
                    self.log("Nenhuma cidade encontrada com este nome.")
                    conn.close()
                    return False

            # Construir query de contagem sem JOIN
            count_conditions = []
            if municipio_codes:
                placeholders = ",".join(["?"] * len(municipio_codes))
                count_conditions.append(f"municipio IN ({placeholders})")
            
            if filters_dict.get("UF"):
                count_conditions.append(f"uf = ?")
            
            if filters_dict.get("CNAE"):
                cnae_input = str(filters_dict["CNAE"]).replace(';', ',')
                cnae_list = [c.strip() for c in cnae_input.split(',') if c.strip()][:5]
                if cnae_list:
                    cnae_subparts = ["cnae_fiscal LIKE ?"] * len(cnae_list)
                    count_conditions.append(f"({' OR '.join(cnae_subparts)})")
            
            if filters_dict.get("SITUAÇÃO"):
                s_map = {'ATIVA': '02', 'BAIXADA': '08', 'SUSPENSA': '03', 'INAPTA': '04', 'NULA': '01'}
                val = str(filters_dict["SITUAÇÃO"]).upper().strip()
                code = s_map.get(val, val)
                count_conditions.append(f"situacao_cadastral = ?")

            # Valores para o count
            count_params = []
            if municipio_codes: count_params.extend(municipio_codes)
            if filters_dict.get("UF"): count_params.append(str(filters_dict["UF"]).upper().strip())
                
            cnae_input = str(filters_dict.get("CNAE", "")).replace(';', ',')
            cnae_list = [c.strip() for c in cnae_input.split(',') if c.strip()][:5]
            for c in cnae_list:
                count_params.append(f"%{c}%")
            
            if filters_dict.get("SITUAÇÃO"):
                val = str(filters_dict["SITUAÇÃO"]).upper().strip()
                count_params.append(s_map.get(val, val))

            count_where = "WHERE " + " AND ".join(count_conditions) if count_conditions else ""

            # 1. Contagem prévia OTIMIZADA
            total_records = 1
            try:
                if not has_excel_filter:
                    with sqlite3.connect(db_path, timeout=5.0) as conn_count:
                        conn_count.execute("PRAGMA query_only = ON")
                        cursor = conn_count.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM estabelecimento {count_where}", count_params)
                        total_records = cursor.fetchone()[0]
                        
                        if limit and limit < total_records:
                            total_records = limit
                            self.log(f"Volume limitado para extração: {limit} registros.")
                        else:
                            self.log(f"Volume identificado: {total_records} registros.")
                else:
                    self.log("Extração por Lote Dinâmico. Iniciando streaming contínuo...")
            except Exception as e:
                self.log(f"Contagem ignorada: {e}")

            if total_records == 0 and not has_excel_filter:
                self.log("Nenhum registro encontrado.")
                if 'conn' in locals():
                    try: conn.close()
                    except: pass
                return False

            # 2. Query Principal Otimizada
            query = f"""
            SELECT 
                e.razao_social, 
                estab.cnpj_basico,
                estab.cnpj_ordem,
                estab.cnpj_dv,
                CASE estab.situacao_cadastral 
                    WHEN '01' THEN 'NULA' WHEN '02' THEN 'ATIVA' WHEN '03' THEN 'SUSPENSA' 
                    WHEN '04' THEN 'INAPTA' WHEN '08' THEN 'BAIXADA' ELSE estab.situacao_cadastral 
                END AS SITUACAO,
                estab.uf,
                m.descricao AS municipio_nome,
                estab.ddd1,
                estab.telefone1,
                estab.ddd2,
                estab.telefone2,
                estab.correio_eletronico,
                estab.tipo_logradouro,
                estab.logradouro,
                estab.numero,
                estab.complemento,
                estab.bairro,
                estab.cep,
                estab.cnae_fiscal,
                cn.descricao AS cnae_descricao
            FROM estabelecimento estab
            {join_excel}
            LEFT JOIN empresas e ON estab.cnpj_basico = e.cnpj_basico
            LEFT JOIN municipio m ON estab.municipio = m.codigo
            LEFT JOIN cnae cn ON estab.cnae_fiscal = cn.codigo
            {where_clause}
            """
            
            self.log("Executando extração de alta performance...")
            
            chunk_list = []
            it = pd.read_sql_query(query, conn, params=main_params, chunksize=50000)
            
            total_rows_accumulated = 0
            for chunk in it:
                if self.stop_requested: break
                
                # Formatação rápida do chunk
                chunk['CNPJ'] = chunk['cnpj_basico'] + chunk['cnpj_ordem'] + chunk['cnpj_dv']
                # Aplica filtro de tipo de telefone, se exigido
                tipo_req = str(filters_dict.get("TIPO_TELEFONE", "")).upper().strip()
                if not tipo_req: tipo_req = "TODOS"
                
                # REMOVIDO: Filtro precoce por telefone1/2 (pode falhar se tiver lixo)
                # O filtro real será feito após o cálculo de TEL_P abaixo
                
                # --- VETORIZAÇÃO: ENDEREÇO ---
                tipo_log_str = chunk['tipo_logradouro'].fillna('').astype(str).str.strip().replace('None', '')
                log_str = chunk['logradouro'].fillna('').astype(str).str.strip().replace('None', '')
                chunk['LOGRADOURO'] = (tipo_log_str + ' ' + log_str).str.strip()
                chunk['NUMERO'] = chunk['numero'].fillna('').astype(str).str.strip().replace('None', '')
                chunk['COMPLEMENTO'] = chunk['complemento'].fillna('').astype(str).str.strip().replace('None', '')
                chunk['BAIRRO'] = chunk['bairro'].fillna('').astype(str).str.strip().replace('None', '')
                
                if 'municipio_nome' not in chunk.columns: chunk['municipio_nome'] = ''
                mun_nome = chunk['municipio_nome'].fillna('').astype(str).str.strip().replace('None', '')
                if 'municipio' in chunk.columns:
                    mun_cod = chunk['municipio'].fillna('').astype(str).str.strip().replace('None', '')
                    chunk['CIDADE'] = mun_nome.where(mun_nome != '', mun_cod)
                else:
                    chunk['CIDADE'] = mun_nome
                
                chunk['UF_END'] = chunk['uf'].fillna('').astype(str).str.strip().replace('None', '')
                chunk['CEP'] = chunk['cep'].fillna('').astype(str).str.strip().replace('None', '')

                # --- VETORIZAÇÃO: E-MAIL E CONTATO ---
                email = chunk['correio_eletronico'].fillna('').astype(str).str.strip().str.lower()
                chunk['EMAIL_P'] = email.where((email != 'none') & (email != ''), '')
                
                def extract_digits(s): return s.fillna('').astype(str).str.replace(r'\D', '', regex=True)
                d1, t1 = extract_digits(chunk['ddd1']), extract_digits(chunk['telefone1'])
                d2, t2 = extract_digits(chunk['ddd2']), extract_digits(chunk['telefone2'])

                def get_phone_info(d, t):
                    v_valid = t.str.len() == 8
                    v_first = t.str[:1]
                    is_cel = v_valid & v_first.isin(['1', '5', '6', '7', '8', '9'])
                    is_fix = v_valid & v_first.isin(['2', '3', '4'])
                    is_cel9 = (t.str.len() == 9)
                    
                    tipo = pd.Series("", index=t.index)
                    tipo.loc[is_cel | is_cel9] = "CELULAR"
                    tipo.loc[is_fix] = "FIXO"
                    
                    t_fmt = pd.Series("", index=t.index)
                    t_fmt.loc[is_cel] = "9" + t.loc[is_cel]
                    t_fmt.loc[is_fix | is_cel9] = t.loc[is_fix | is_cel9]
                    
                    return d, t_fmt, tipo

                d1, t1_fmt, tipo1 = get_phone_info(d1, t1)
                d2, t2_fmt, tipo2 = get_phone_info(d2, t2)

                # Se a solicitação for AMBOS, filtramos apenas quem tem Celular E Fixo (em qualquer uma das colunas)
                if tipo_req == "AMBOS":
                    has_cel = (tipo1 == "CELULAR") | (tipo2 == "CELULAR")
                    has_fix = (tipo1 == "FIXO") | (tipo2 == "FIXO")
                    chunk = chunk[has_cel & has_fix].copy()
                    # Re-calcular d1, t1_fmt etc após o filter pra manter index alinhado
                    d1, t1_fmt, tipo1 = d1.loc[chunk.index], t1_fmt.loc[chunk.index], tipo1.loc[chunk.index]
                    d2, t2_fmt, tipo2 = d2.loc[chunk.index], t2_fmt.loc[chunk.index], tipo2.loc[chunk.index]
                elif tipo_req in ["CELULAR", "FIXO"]:
                    # Se for específico, filtramos quem tem pelo menos um do tipo
                    has_type = (tipo1 == tipo_req) | (tipo2 == tipo_req)
                    chunk = chunk[has_type].copy()
                    d1, t1_fmt, tipo1 = d1.loc[chunk.index], t1_fmt.loc[chunk.index], tipo1.loc[chunk.index]
                    d2, t2_fmt, tipo2 = d2.loc[chunk.index], t2_fmt.loc[chunk.index], tipo2.loc[chunk.index]
                    
                    # --- PRIORIZAÇÃO DE POSIÇÃO ---
                    # Se o tipo solicitado estiver no slot 2 mas NÃO no 1, fazemos o swap para que apareça em TELEFONE 1
                    needs_swap = (tipo1 != tipo_req) & (tipo2 == tipo_req)
                    if needs_swap.any():
                        # Backup de slot 1 
                        sd1, st1, stip1 = d1[needs_swap].copy(), t1_fmt[needs_swap].copy(), tipo1[needs_swap].copy()
                        # Move slot 2 -> 1
                        d1.loc[needs_swap] = d2[needs_swap]
                        t1_fmt.loc[needs_swap] = t2_fmt[needs_swap]
                        tipo1.loc[needs_swap] = tipo2[needs_swap]
                        # Move backup -> 2 (Swap completo)
                        d2.loc[needs_swap] = sd1
                        t2_fmt.loc[needs_swap] = st1
                        tipo2.loc[needs_swap] = stip1

                chunk['DDD1_P'], chunk['TEL1_P'], chunk['TIPO1_P'] = d1, t1_fmt, tipo1
                chunk['DDD2_P'], chunk['TEL2_P'], chunk['TIPO2_P'] = d2, t2_fmt, tipo2
                
                # Suporte ao filtro de telefone (Apenas quem tem)
                if somente_tel:
                    # Aplica o filtro nuclear hardened: pelo menos um telefone válido
                    orig_count = len(chunk)
                    val1 = chunk['TEL1_P'].apply(self._is_valid_phone)
                    val2 = chunk['TEL2_P'].apply(self._is_valid_phone)
                    chunk = chunk[val1 | val2].copy()
                    disc = orig_count - len(chunk)
                    if disc > 0:
                        self.log(f"    - Bloco: Removidos {disc} registros sem telefone válido.")
                
                if chunk.empty: continue # Se o chunk ficou vazio pós-filtragem, pule.
                
                # --- DINÂMICA DE COLUNAS ---
                base_cols = ['CNPJ', 'razao_social', 'SITUACAO', 'cnae_fiscal', 'LOGRADOURO', 'NUMERO', 'COMPLEMENTO', 'BAIRRO', 'CIDADE', 'UF_END', 'CEP']
                base_names = ['CNPJ', 'RAZÃO SOCIAL', 'SITUAÇÃO', 'CNAE', 'LOGRADOURO', 'NUMERO', 'COMPLEMENTO', 'BAIRRO', 'CIDADE', 'UF', 'CEP']
                
                if tipo_req in ["CELULAR", "FIXO"]:
                    sel_cols = base_cols + ['DDD1_P', 'TEL1_P', 'TIPO1_P', 'EMAIL_P']
                    sel_names = base_names + ['DDD 1', 'TELEFONE 1', 'TIPO 1', 'EMAIL']
                else:
                    sel_cols = base_cols + ['DDD1_P', 'TEL1_P', 'TIPO1_P', 'DDD2_P', 'TEL2_P', 'TIPO2_P', 'EMAIL_P']
                    sel_names = base_names + ['DDD 1', 'TELEFONE 1', 'TIPO 1', 'DDD 2', 'TELEFONE 2', 'TIPO 2', 'EMAIL']
                
                chunk_final = chunk[sel_cols].copy()
                chunk_final.columns = sel_names
                
                # PREVENÇÃO DE DUPLICATAS NÍVEL PANDAS (NUCLEAR):
                chunk_final = chunk_final.drop_duplicates(subset=['CNPJ'])
                
                # Unicidade GLOBAL (entre blocos)
                if not hasattr(self, '_global_seen_cnpjs'):
                    self._global_seen_cnpjs = set()
                
                chunk_final = chunk_final[~chunk_final['CNPJ'].isin(self._global_seen_cnpjs)]
                self._global_seen_cnpjs.update(chunk_final['CNPJ'].tolist())
                
                # --- INTEGRAÇÃO: OPERADORAS ---
                # Identifica as operadoras das colunas de telefone 1 e 2 (DDD + TELEFONE)
                try:
                    t1_full = chunk_final['DDD 1'].astype(str) + chunk_final['TELEFONE 1'].astype(str)
                    chunk_final['OPERADORA 1'] = self._batch_lookup_operators(t1_full)
                    # Enriquecimento opcional da Operadora 2 apenas se a coluna existir
                    if 'TELEFONE 2' in chunk_final.columns:
                        t2_full = chunk_final['DDD 2'].astype(str) + chunk_final['TELEFONE 2'].astype(str)
                        chunk_final['OPERADORA 2'] = self._batch_lookup_operators(t2_full)
                except Exception as e:
                    self.log(f"Aviso regional: Falha ao cruzar operadoras no bloco: {e}")
                    chunk_final['OPERADORA 1'] = ""
                    chunk_final['OPERADORA 2'] = ""

                if chunk_final.empty: continue
                
                chunk_list.append(chunk_final)
                total_rows_accumulated += len(chunk_final)
                
                if self.usage_callback:
                    self.usage_callback(len(chunk_final))
                
                # Feedback de progresso via UI e Console de log corrigido
                if self.progress_callback:
                    self.progress_callback(total_rows_accumulated, total_records)
                
                # Mostrar o log toda vez que o volume aumentar exponencialmente para feedback limpo.
                self.log(f"  -> Processando Bloco... Acumulado filtrado: {total_rows_accumulated} linhas")
            
            # Limpa tracking global
            if hasattr(self, '_global_seen_cnpjs'):
                del self._global_seen_cnpjs
            
            conn.close()
            
            if not chunk_list:
                self.log("Nenhum registro encontrado com estes filtros.")
                return False

            self.log(f"Iniciando gravação no disco de {total_rows_accumulated} registros. (Evite fechar o programa...)")
            
            limite_aba = 1000000 # O Excel aguenta até 1048576
            
            # Se a extensão escolhida pelo usuário for CSV, faz streaming append hiper-rápido.
            if output_file.lower().endswith('.csv'):
                for idx, chunk_df in enumerate(chunk_list):
                    mode = 'w' if idx == 0 else 'a'
                    header = True if idx == 0 else False
                    chunk_df.to_csv(output_file, mode=mode, header=header, index=False, sep=';', encoding='utf-8-sig')
            else:
                # Exportação Excel: Ativamos 'constant_memory' no xlsxwriter, mas fazemos write linha a linha
                # porque df.to_excel do pandas ignora isso para bulk write e pula as colunas em certas versões.
                import xlsxwriter
                workbook = xlsxwriter.Workbook(output_file, {'constant_memory': True, 'nan_inf_to_errors': True})
                current_sheet = 1
                current_row = 1
                worksheet = workbook.add_worksheet(f"Lote {current_sheet}")
                header_written = False
                
                for chunk_df in chunk_list:
                    if self.stop_requested: break
                    
                    if not header_written:
                        cols = chunk_df.columns.tolist()
                        worksheet.write_row(0, 0, cols)
                        header_written = True
                    
                    # Sanitize before write to avoid xlsxwriter errors
                    chunk_df = chunk_df.fillna('').astype(str)
                    
                    for r_data in chunk_df.itertuples(index=False):
                        if current_row > limite_aba:
                            current_sheet += 1
                            current_row = 1
                            worksheet = workbook.add_worksheet(f"Lote {current_sheet}")
                            worksheet.write_row(0, 0, cols)
                            self.log(f"  -> Gerando nova aba no Excel: 'Lote {current_sheet}'...")
                            
                        worksheet.write_row(current_row, 0, r_data)
                        current_row += 1
                        
                workbook.close()
            
            # Forçando limpeza de listas pesadas
            del chunk_list
            
            self.log(f"Extração concluída com sucesso! Salvo em: {os.path.basename(output_file)}")
            self.log(f"Tempo total: {time.time() - start_time:.2f} segundos.")
            return True
            
        except Exception as e:
            self.log(f"Erro na extração filtrada: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                try: conn.close()
                except: pass

    def _batch_lookup_operators(self, telefones):
        """
        Realiza a busca de operadoras para uma série de telefones de forma otimizada.
        """
        if telefones.empty:
            return pd.Series([], dtype=str)
            
        db_path = r"C:\HEMN_SYSTEM_DB\hemn_carrier.db"
        results_dict = {}
        
        # 1. Limpeza e normalização rápida
        search_series = telefones.fillna("").astype(str).str.replace(r'\D+', '', regex=True)
        # Normalização BR (Remove 55 inicial ou 0 se necessário para bater no DB)
        # O DB costuma guardar com DDD (10 ou 11 dígitos)
        
        unique_phones = search_series.drop_duplicates().tolist()
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                chunk_sql = 10000
                for i in range(0, len(unique_phones), chunk_sql):
                    sub_phones = unique_phones[i:i+chunk_sql]
                    placeholders = ','.join(['?'] * len(sub_phones))
                    query = f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})"
                    cursor = conn.execute(query, sub_phones)
                    for tel, operadora_id in cursor.fetchall():
                        results_dict[tel] = self.get_carrier_name(operadora_id)
                conn.close()
            except:
                pass

        # 2. Identificação por Prefixo (Fallback/Portado não encontrado)
        final_results = []
        for tel in search_series:
            if not tel or len(tel) < 8:
                final_results.append("")
                continue
                
            res = results_dict.get(tel)
            if not res or res == 'NÃO CONSTA NA BASE' or 'CÓD' in str(res):
                res = self.identify_original_carrier(tel)
            
            final_results.append(res)
            
        return pd.Series(final_results, index=telefones.index)

    def split_large_file(self, input_path, output_path):
        """
        Divide um arquivo tabular gigante (CSV ou Excel) em múltiplas abas num arquivo Excel final,
        respeitando o limite de 1 Milhão de linhas por aba via streaming de memória constante.
        """
        import os
        import time
        
        start_time = time.time()
        self.log(f"Iniciando divisor de arquivo gigante...")
        self.stop_requested = False
        
        limite_aba = 1000000 # Excel max size by sheet
        
        try:
            # 1. Obter o iterator de leitura com base no arquivo de entrada
            ext = input_path.lower()
            iterator = None
            total_estimated = 0
            
            if ext.endswith('.csv'):
                self.log("Detectado formato CSV. Preparando leitura particionada...")
                # Tentar inferir separador lendo a primeira linha
                with open(input_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                sep = ';' if ';' in first_line else ','
                iterator = pd.read_csv(input_path, chunksize=100000, sep=sep, encoding='utf-8', on_bad_lines='skip', dtype=str)
                # Estimativa baseada no tamanho do arquivo
                fs = os.path.getsize(input_path)
                total_estimated = int(fs / 200) # Assumindo 200 bytes por linha
            elif ext.endswith(('.xlsx', '.xls')):
                self.log("Detectado formato Excel. Atenção: A leitura do Excel inteiro consome bastante Memória RAM.")
                df = pd.read_excel(input_path, dtype=str)
                # Mockando um iterator pra manter a mesma lógica fluída
                total_estimated = len(df)
                iterator = (df.iloc[i:i+100000] for i in range(0, total_estimated, 100000))
            else:
                self.log(f"Formato de arquivo não suportado: {ext}")
                return False

            import xlsxwriter
            self.log(f"Iniciando gravação no disco particionada... (Aba Limite: {limite_aba})")
            
            workbook = xlsxwriter.Workbook(output_path, {'constant_memory': True, 'nan_inf_to_errors': True})
            current_sheet = 1
            current_row = 1
            worksheet = workbook.add_worksheet(f"Sub_Lote {current_sheet}")
            header_written = False
            total_processado = 0
            
            for chunk in iterator:
                if self.stop_requested:
                    self.log("Divisão interrompida pelo usuário.")
                    break
                
                if not header_written:
                    cols = chunk.columns.tolist()
                    worksheet.write_row(0, 0, cols)
                    header_written = True
                
                # Treat nan and types to bypass Excel xml failures
                chunk = chunk.fillna('').astype(str)
                
                for r_data in chunk.itertuples(index=False):
                    if current_row > limite_aba:
                        current_sheet += 1
                        current_row = 1
                        worksheet = workbook.add_worksheet(f"Sub_Lote {current_sheet}")
                        worksheet.write_row(0, 0, cols)
                        self.log(f"  -> Gerando aba 'Sub_Lote {current_sheet}'...")
                        
                    worksheet.write_row(current_row, 0, r_data)
                    current_row += 1
                
                chunk_len = len(chunk)
                total_processado += chunk_len
                
                if self.progress_callback:
                    p_val = total_processado if ext.endswith('.csv') else total_processado
                    t_val = max(total_estimated, total_processado) 
                    self.progress_callback(p_val, t_val)
                
                self.log(f"  -> Lidos e transpostos: {total_processado} registros...")
                
            workbook.close()
                    
            self.log(f"Divisão concluída com sucesso! Geradas {current_sheet} abas.")
            self.log(f"Tempo total de divisão: {time.time() - start_time:.2f} segundos.")
            return True
            
        except Exception as e:
            self.log(f"Erro no Divisor de Arquivos: {e}")
            return False
        finally:
            if 'conn' in locals():
                try: conn.close()
                except: pass

    def import_carrier_csv(self, csv_path):
        """
        Lê e importa o CSV de Portabilidade Anatel (gigante) para um banco SQLite local.
        (ex: exporta.csv)
        """
        db_dir = r"C:\HEMN_SYSTEM_DB"
        if not os.path.exists(db_dir): os.makedirs(db_dir)
        db_path = os.path.join(db_dir, "hemn_carrier.db")
        self.log(f"Iniciando conversão do CSV de Portabilidade para SQLite: {db_path}")
        
        try:
            # Cria a tabela
            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS portabilidade (
                        telefone TEXT PRIMARY KEY,
                        operadora_id TEXT
                    )
                ''')
                conn.execute("PRAGMA synchronous = OFF") # Ultra performance mode
                conn.execute("PRAGMA journal_mode = MEMORY")
            
            # Lê em chunks
            chunk_size = 500000 
            total_processado = 0
            
            # Estrutura do exporta.csv: ID ; Telefone ; Código da Operadora ; Data
            # Ex: 2334;7133015216;55131;2008-09-03 01:00:08
            for chunk in pd.read_csv(csv_path, sep=';', chunksize=chunk_size, 
                                     engine='c', usecols=[1, 2], names=['telefone', 'operadora_id'], 
                                     dtype=str, header=None):
                
                if self.stop_requested:
                    self.log("Importação cancelada.")
                    break
                
                with sqlite3.connect(db_path) as conn:
                    # Remove duplicatas se tiver o mesmo telefone
                    chunk = chunk.drop_duplicates(subset=['telefone'], keep='last')
                    try:
                        chunk.to_sql('portabilidade', conn, if_exists='append', index=False)
                    except sqlite3.IntegrityError:
                        pass # Ignore duplicates hitting index during append
                    
                total_processado += len(chunk)
                self.log(f"  -> Inseridos: {total_processado} números...")
                
                if self.progress_callback:
                    # Usando um total arbitrário grande pra barra fluir, ou não precisa.
                    self.progress_callback(total_processado, 55000000)
            
            self.log("Criando índices de busca em alta velocidade...")
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_portabilidade_tel ON portabilidade(telefone)")
                conn.execute("VACUUM") # Otimiza arquivo final
            
            self.log(f"Importação de Operadoras concluída! ({total_processado} números)")
            if self.progress_callback:
                self.progress_callback(100, 100)
            return True
            
        except Exception as e:
            self.log(f"Erro na conversão CSV -> Banco SQLite: {e}")
            return False

    def _load_data_assets(self):
        """ Carrega dicionário de operadoras e base de prefixos localmente """
        self.anatel_dict = {}
        self.prefix_tree = [] # Lista de (prefixo, empresa) ordenada por comprimento decrescente
        
        # Assets ficam na pasta data_assets ao lado do script ou no MEIPASS
        assets_dir = resource_path("data_assets")
        dict_path = os.path.join(assets_dir, "cod_operadora.csv")
        prefix_path = os.path.join(assets_dir, "prefix_anatel.csv")
        
        # Se não existir no resource_path, tenta no diretório atual (desenvolvimento)
        if not os.path.exists(dict_path):
            dict_path = os.path.join(os.path.dirname(__file__), "data_assets", "cod_operadora.csv")
        if not os.path.exists(prefix_path):
            prefix_path = os.path.join(os.path.dirname(__file__), "data_assets", "prefix_anatel.csv")
        
        # 1. Carregar Dicionário de Operadoras
        if os.path.exists(dict_path):
            try:
                # Arquivos da Diamond costumam usar latin1/iso-8859-1 para acentos
                with open(dict_path, mode='r', encoding='latin1') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            self.anatel_dict[row[0].strip()] = row[1].strip()
                self.log(f"Dicionário de operadoras carregado: {len(self.anatel_dict)} registros.")
            except Exception as e:
                self.log(f"Erro ao carregar dicionário de operadoras: {e}")
        
        # Fallback para as principais se o arquivo falhar ou não existir
        if not self.anatel_dict:
            self.anatel_dict = {
                "55320": "VIVO", "55310": "VIVO", "55323": "VIVO", "55321": "CLARO", "55341": "TIM", "55312": "ALGAR", "55331": "OI"
            }
            
        # 2. Carregar Base de Prefixos (103k registros)
        if os.path.exists(prefix_path):
            try:
                # Usar dicionário de prefixos para busca O(1)
                self.prefix_tree = {} # {prefixo: company_code}
                df_prefix = pd.read_csv(prefix_path, sep=';', dtype=str)
                if 'number' in df_prefix.columns and 'company' in df_prefix.columns:
                    for _, row in df_prefix.iterrows():
                        self.prefix_tree[row['number'].strip()] = row['company'].strip()
                    self.log(f"Base de prefixos carregada: {len(self.prefix_tree)} registros (Hash Mode).")
            except Exception as e:
                self.log(f"Erro ao carregar base de prefixos: {e}")

    def get_carrier_name(self, carrier_code):
        """ Retorna o nome da operadora com base no código RN1/Anatel """
        if not hasattr(self, 'anatel_dict'):
            self._load_data_assets()
            
        code = str(carrier_code).strip()
        return self.anatel_dict.get(code, f"CÓD {code}")

    def identify_original_carrier(self, phone):
        """ Identificação REAL por prefixo usando busca O(1) via dicionário """
        if not hasattr(self, 'prefix_tree') or not self.prefix_tree:
            self._load_data_assets()
            
        # Cache Check
        if not hasattr(self, '_carrier_cache'): self._carrier_cache = {}
        if phone in self._carrier_cache: return self._carrier_cache[phone]
            
        num = re.sub(r'\D', '', str(phone))
        # Normalização básica (tira 55 e 0)
        if num.startswith("55") and len(num) >= 12: num = num[2:]
        if num.startswith("0"): num = num[1:]
        
        if len(num) < 10: return "INVÁLIDO"
        
        # Estratégia O(1): Testa prefixos do maior para o menor (7 a 4 dígitos)
        # Mais rápido que iterar 103k registros 
        def lookup(n):
            for length in range(7, 3, -1):
                pref = n[:length]
                if pref in self.prefix_tree:
                    return self.get_carrier_name(self.prefix_tree[pref])
            return None

        res = lookup(num)
        
        # Fallback para Celulares (Brasil): Tenta ignorar o 9º dígito se for 11 dígitos e começar com DDD + 9
        if not res and len(num) == 11 and num[2] == '9':
            num_8digito = num[:2] + num[3:] # Remove o 9
            res = lookup(num_8digito)
        
        final_res = res if res else "NÃO CONSTA NA BASE"
        self._carrier_cache[phone] = final_res
        return final_res

    # Identificação por prefixo atua como fallback quando o número não é encontrado no banco de portabilidade

    def process_carrier_lookup(self, input_excel, phone_column, output_excel, limit=None):
        """
        Lê uma planilha, captura a coluna de telefone, bate no SQLite hemn_carrier.db
        e gera uma planilha nova com a coluna "OPERADORA_PORTABILIDADE".
        """
        db_path = r"C:\HEMN_SYSTEM_DB\hemn_carrier.db"
        if not os.path.exists(db_path):
            self.log("ERRO FATAL: Banco de dados hemn_carrier.db não encontrado. Faça a importação primeiro.")
            return False
            
        self.log(f"Lendo planilha: {input_excel} (Coluna: {phone_column})...")
        try:
            # Força str para preservar zeros a esquerda, ignora tipos zoado
            if input_excel.endswith('.csv'):
                # Ler em chunks se for muito grande para não estourar RAM, mas aqui lemos o necessário
                df = pd.read_csv(input_excel, sep=None, engine='python', dtype=str)
            else:
                df = pd.read_excel(input_excel, dtype=str)
                
            if phone_column not in df.columns:
                self.log(f"A coluna '{phone_column}' não foi encontrada na planilha!")
                return False
            
            # Aplicar limite se solicitado
            if limit and limit < len(df):
                df = df.head(limit)
                self.log(f"Limitando extração para os primeiros {limit} registros conforme solicitado.")

            # Limpa e converte a coluna original numa nova pra pesquisa
            df['_search_tel'] = df[phone_column].fillna("").astype(str)
            # Remove o que não é número (parênteses, traços, etc)
            df['_search_tel'] = df['_search_tel'].str.replace(r'\D+', '', regex=True)
            
            # Normalização BR
            # Remove o +55 do começo, Remove 0 do DDD
            df['_search_tel'] = df['_search_tel'].apply(
                lambda x: x[2:] if x.startswith("55") and len(x) >= 12 else x
            )
            df['_search_tel'] = df['_search_tel'].apply(
                lambda x: x[1:] if x.startswith("0") else x
            )
            
            self.log(f"Identificados {len(df)} registros. Cruzando com banco de portabilidade oculto...")
            
            conn = sqlite3.connect(db_path)
            
            unique_phones = df['_search_tel'].drop_duplicates().tolist()
            # Bater todos de uma vez dividindo em chunks (se forem muitos)
            results_dict = {} # {numero: operadora}
            
            chunk_sql = 10000
            total_phones = len(unique_phones)
            
            for i in range(0, total_phones, chunk_sql):
                if self.stop_requested:
                    self.log("Busca de Operadora cancelada.")
                    conn.close()
                    return False
                    
                sub_phones = unique_phones[i:i+chunk_sql]
                placeholders = ','.join(['?'] * len(sub_phones))
                query = f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})"
                
                cursor = conn.execute(query, sub_phones)
                for tel, operadora_id in cursor.fetchall():
                    results_dict[tel] = self.get_carrier_name(operadora_id)
                
                if self.progress_callback:
                    self.progress_callback(i, total_phones)
                    
            conn.close()
            
            # Mapeia os resultados de volta
            df['OPERADORA_PORTABILIDADE'] = df['_search_tel'].map(results_dict)
            
            # Identificação de Origem para quem não foi portado
            self.log("Aplicando identificação por prefixo oficial (Anatel) para remanescentes...")
            def fill_original(row):
                if pd.isna(row['OPERADORA_PORTABILIDADE']) or row['OPERADORA_PORTABILIDADE'] == 'NÃO CONSTA NA BASE' or 'CÓD' in str(row['OPERADORA_PORTABILIDADE']):
                    return self.identify_original_carrier(row['_search_tel'])
                return row['OPERADORA_PORTABILIDADE']
                
            df['OPERADORA_PORTABILIDADE'] = df.apply(fill_original, axis=1)
            
            # Remove a coluna temporária
            df = df.drop(columns=['_search_tel'])
            
            self.log(f"Cruzamento concluído! Salvando arquivo: {output_excel}")
            
            # Exporta pro layout final
            engine_args = {'engine': 'xlsxwriter'}
            df.to_excel(output_excel, index=False, **engine_args)
            
            if self.progress_callback:
                self.progress_callback(100, 100)
            self.log("SUCESSO: Tabela de Operadoras gerada!")
            return True
            
        except Exception as e:
            self.log(f"Erro na rotina de Busca de Operadora: {e}")
            return False
