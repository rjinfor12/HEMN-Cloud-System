import pandas as pd
import os
import re

class CoverageEngine:
    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.stop_requested = False

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        print(f"[CoverageEngine] {msg}")

    def _update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _clean_number(self, val):
        """ Limpa o número da fachada para conversão em inteiro """
        if pd.isna(val) or str(val).strip().upper() in ['SN', 'S/N', 'S.N', '']:
            return "SN"
        # Extrair apenas dígitos
        nums = re.findall(r'\d+', str(val))
        if nums:
            return int(nums[0])
        return "SN"

    def _clean_cep(self, val):
        """ Limpa o CEP para string de 8 dígitos """
        if pd.isna(val): return ""
        c = re.sub(r'\D', '', str(val))
        return c.zfill(8)[:8]

    def process_coverage(self, cnpj_file, vivo_files, filter_tipo="TODOS"):
        """
        Realiza o cruzamento geográfico.
        cnpj_file: Caminho do arquivo de CNPJs.
        vivo_files: Lista de caminhos de arquivos da Vivo.
        filter_tipo: TODOS, HORIZONTAL, VERTICAL.
        """
        try:
            self.stop_requested = False
            self._log(f"Iniciando cruzamento geográfico (Filtro: {filter_tipo})...")

            # 1. Carregar Base CNPJ (Todas as abas)
            self._log(f"Lendo base CNPJ: {os.path.basename(cnpj_file)}...")
            cnpj_df = self._read_all_sheets(cnpj_file)
            if cnpj_df.empty:
                self._log("Erro: Base CNPJ vazia ou não encontrada.")
                return None

            # Normalizar colunas CNPJ (mapeando conforme o print do usuário)
            # CNPJ: CEP, NUMERO
            cnpj_df.columns = [c.upper() for c in cnpj_df.columns]
            col_cep_cnpj = next((c for c in cnpj_df.columns if "CEP" in c), None)
            col_num_cnpj = next((c for c in cnpj_df.columns if "NUMERO" in c), None)

            if not col_cep_cnpj or not col_num_cnpj:
                self._log(f"Erro: Colunas 'CEP' ou 'NUMERO' não encontradas no CNPJ. Colunas: {list(cnpj_df.columns)}")
                return None

            # Pré-processar CNPJ
            cnpj_df['CEP_NORM'] = cnpj_df[col_cep_cnpj].apply(self._clean_cep)
            cnpj_df['NUM_NORM'] = cnpj_df[col_num_cnpj].apply(self._clean_number)

            # 2. Carregar Bases Vivo (Todas as abas de todos os arquivos)
            vivo_full_df = pd.DataFrame()
            for v_file in vivo_files:
                self._log(f"Lendo base Vivo: {os.path.basename(v_file)}...")
                v_df = self._read_all_sheets(v_file)
                vivo_full_df = pd.concat([vivo_full_df, v_df], ignore_index=True)

            if vivo_full_df.empty:
                self._log("Erro: Bases Vivo vazias ou não encontradas.")
                return None

            # Normalizar colunas Vivo (UF, CIDADE, ARMARIO, TERRITORI, LOGRADO, NUM, CEP, BAIRRO, TIPO, CHAVE)
            vivo_full_df.columns = [c.upper() for c in vivo_full_df.columns]
            col_cep_vivo = next((c for c in vivo_full_df.columns if "CEP" in c), None)
            col_num_vivo = next((c for c in vivo_full_df.columns if "NUM" in c and "NUMERO" not in c) or (c for c in vivo_full_df.columns if "NUM" in c), None)
            col_tipo_vivo = next((c for c in vivo_full_df.columns if "TIPO" in c), None)

            if not col_cep_vivo or not col_num_vivo:
                self._log("Erro: Colunas 'CEP' ou 'NUM' não encontradas na base Vivo.")
                return None

            # Aplicar filtro de TIPO na origem para ganhar performance
            if filter_tipo != "TODOS" and col_tipo_vivo:
                # Na planilha do usuário está "HORIZONT", na UI "HORIZONTAL"
                filter_val = filter_tipo[:7].upper() # Pega "HORIZON" ou "VERTICA"
                vivo_full_df = vivo_full_df[vivo_full_df[col_tipo_vivo].astype(str).str.upper().str.contains(filter_val)]
                self._log(f"Filtro '{filter_tipo}' aplicado. {len(vivo_full_df)} registros de cobertura restantes.")

            # Pré-processar Vivo
            vivo_full_df['CEP_NORM'] = vivo_full_df[col_cep_vivo].apply(self._clean_cep)
            vivo_full_df['NUM_NORM'] = vivo_full_df[col_num_vivo].apply(self._clean_number)

            # 3. Cruzamento Geográfico
            self._log("Cruzando dados por CEP, Proximidade e Paridade...")
            results = []
            total_cnpj = len(cnpj_df)
            
            # Criar dicionário de busca rápida por CEP na base Vivo
            vivo_dict = {}
            for _, row in vivo_full_df.iterrows():
                cep = row['CEP_NORM']
                if cep not in vivo_dict:
                    vivo_dict[cep] = []
                vivo_dict[cep].append(row)

            for i, (_, row_c) in enumerate(cnpj_df.iterrows()):
                if self.stop_requested: break
                if i % 100 == 0:
                    self._update_progress(i, total_cnpj)

                cep_c = row_c['CEP_NORM']
                num_c = row_c['NUM_NORM']

                if cep_c in vivo_dict:
                    matches = vivo_dict[cep_c]
                    for row_v in matches:
                        num_v = row_v['NUM_NORM']
                        
                        is_match = False
                        match_obs = ""

                        # Regra 1: CEP Match Exato (Já garantido pelo dict)
                        
                        # Regra 2: Paridade e Proximidade (Se ambos forem números)
                        if isinstance(num_c, int) and isinstance(num_v, int):
                            # Mesma Paridade: (n1 % 2) == (n2 % 2)
                            if (num_c % 2) == (num_v % 2):
                                # Proximidade: abs(diff) <= 20
                                if abs(num_c - num_v) <= 20:
                                    is_match = True
                                    match_obs = f"PROXIMIDADE (Diff: {abs(num_c - num_v)})"
                        
                        # Regra 3: SN match SN
                        elif num_c == "SN" and num_v == "SN":
                            is_match = True
                            match_obs = "MATCH SN"
                        
                        # Regra 4: Match Exato (Caso não sejam puramente numéricos mas strings iguais)
                        elif str(num_c).strip() == str(num_v).strip():
                            is_match = True
                            match_obs = "NUMERO EXATO"

                        if is_match:
                            # Unir dados para exportação
                            out_row = row_c.to_dict()
                            # Renomear colunas do vivo para evitar colisão
                            for k, v in row_v.to_dict().items():
                                if k not in ['CEP_NORM', 'NUM_NORM']:
                                    out_row[f"VIVO_{k}"] = v
                            out_row['OBS_CRUZAMENTO'] = match_obs
                            results.append(out_row)
                            # Se encontrou um match assertivo, para de procurar no mesmo CEP? 
                            # Usuário não especificou, geralmente queremos todas as opções de porta.
                            # Para evitar duplicar o CNPJ demais, vamos pegar o melhor match ou todos?
                            # No print dele parece querer enriquecer. Vamos manter todos por enquanto.

            self._update_progress(total_cnpj, total_cnpj)
            
            if not results:
                self._log("Nenhum cruzamento encontrado com as regras de paridade/proximidade.")
                return pd.DataFrame()

            res_df = pd.DataFrame(results)
            self._log(f"Sucesso! {len(res_df)} cruzamentos validados encontrados.")
            return res_df

        except Exception as e:
            self._log(f"Erro no Motor de Cruzamento: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            return None

    def _read_all_sheets(self, file_path):
        """ Lê todas as abas de um arquivo Excel e une em um DataFrame único """
        if file_path.lower().endswith('.csv'):
            return pd.read_csv(file_path, dtype=str)
        
        xl = pd.ExcelFile(file_path)
        dfs = []
        for sheet in xl.sheet_names:
            self._log(f"  -> Lendo aba: {sheet}")
            dfs.append(xl.parse(sheet, dtype=str))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def export_partitioned(self, df, base_path):
        """ Exporta o resultado em lotes de 900k para evitar limites do Excel """
        if df.empty: return
        
        chunk_size = 900000
        total = len(df)
        
        if total <= chunk_size:
            df.to_excel(base_path, index=False)
            self._log(f"Resultado salvo em: {base_path}")
        else:
            num_chunks = (total // chunk_size) + 1
            self._log(f"Resultado grande ({total} linhas). Particionando em {num_chunks} arquivos...")
            for i in range(num_chunks):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, total)
                chunk_df = df.iloc[start:end]
                
                path_parts = os.path.splitext(base_path)
                chunk_path = f"{path_parts[0]}_PART_{i+1}{path_parts[1]}"
                chunk_df.to_excel(chunk_path, index=False)
                self._log(f"  -> Parte {i+1} salva: {os.path.basename(chunk_path)}")
