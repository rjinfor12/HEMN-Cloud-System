
import pandas as pd
import numpy as np
import sqlite3
import re
import os
import time
import threading

class Checkpoint:
    def __init__(self):
        self.db_carrier = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_carrier.db'
        self.prefix_tree = {} # Mock
        
    def _get_carrier_map(self):
        # Reduzido para teste
        return {"55320": "VIVO", "55321": "CLARO"}

    def get_op_name(self, code):
        return "MOCK_OP"

    def _update_task(self, tid, progress, message):
        print(f"Task {tid} - {progress}% - {message}")

    def _append_operator_column(self, tid, df):
        """
        Enriquecimento de operadora de ALTA PERFORMANCE.
        Usa cache em lote e evita processamento linha-a-linha desnecessário.
        """
        if 'TELEFONE SOLICITADO' not in df.columns or df.empty:
            df['OPERADORA DO TELEFONE'] = "NÃO CONSTA"
            return df

        self._update_task(tid, progress=90, message="Identificando operadoras...")
        try:
            # 1. Limpeza Vetorizada de Telefones
            df['_clean_tel_enrich'] = df['TELEFONE SOLICITADO'].astype(str).str.replace(r'\D', '', regex=True).str.replace(r'^55', '', regex=True)
            
            unique_phones = df['_clean_tel_enrich'].unique()
            phones_to_query = [p for p in unique_phones if p and p != 'nan']
            
            # Gerar variações (11 -> 10 para portabilidade legada)
            all_queries = set(phones_to_query)
            for p in phones_to_query:
                if len(p) == 11: all_queries.add(p[:2] + p[3:]) # DDD + 8 dígitos
            
            # 2. Consulta SQLite em Lotes (Cache de Resultados)
            op_results = {}
            op_map = self._get_carrier_map()
            
            all_queries_list = list(all_queries)
            batch_size = 1000  # Aumentado para melhor performance
            
            # OTIMIZAÇÃO CRÍTICA: Abrir conexão UMA VEZ
            conn = sqlite3.connect(self.db_carrier)
            cursor = conn.cursor()
            
            total_queries = len(all_queries_list)
            for i in range(0, total_queries, batch_size):
                # PROGRESS FEEDBACK
                if i % 5000 == 0:
                   p_val = 90 + int((i/total_queries) * 9)
                   self._update_task(tid, progress=p_val, message=f"Consultando Operadoras: {i:,}/{total_queries:,}...")

                batch = all_queries_list[i : i + batch_size]
                placeholders = ','.join(['?'] * len(batch))
                rows = cursor.execute(f"SELECT telefone, operadora_id FROM portabilidade WHERE telefone IN ({placeholders})", batch).fetchall()
                for tel_db, op_id in rows:
                    op_results[str(tel_db)] = op_map.get(str(op_id), "OUTRA")
            
            conn.close()

            # 3. Mapeamento Inteligente e Fallback de Prefixo (Híbrido Vetorizado)
            # Primeiro nível: Mapeamento direto da Portabilidade
            df['OPERADORA DO TELEFONE'] = df['_clean_tel_enrich'].map(op_results)
            
            # Segundo nível: Portabilidade com 10 dígitos (se o de 11 falhou)
            mask_retry_10 = (df['OPERADORA DO TELEFONE'].isna()) & (df['_clean_tel_enrich'].str.len() == 11)
            if mask_retry_10.any():
                df.loc[mask_retry_10, 'OPERADORA DO TELEFONE'] = (df.loc[mask_retry_10, '_clean_tel_enrich'].str[:2] + df.loc[mask_retry_10, '_clean_tel_enrich'].str[3:]).map(op_results)

            # Terceiro nível: Prefixo Anatel (Fallback)
            mask_prefix = df['OPERADORA DO TELEFONE'].isna() | (df['OPERADORA DO TELEFONE'] == "OUTRA")
            if mask_prefix.any():
                # Loop limitado por comprimentos de prefixo (mais rápido que loop por linha)
                prefix_results = pd.Series(index=df.index, dtype=str)
                nums = df.loc[mask_prefix, '_clean_tel_enrich']
                
                # De 7 a 4 dígitos
                for length in [7, 6, 5, 4]:
                    if nums.empty: break
                    prefs = nums.str[:length]
                    # Mapear prefixos usando o prefix_tree em memória
                    mapped = prefs.map(self.prefix_tree).dropna()
                    if not mapped.empty:
                        # Converter códigos Anatel para nomes reais
                        unique_codes = mapped.unique()
                        code_to_name = {c: self.get_op_name(c).upper() for c in unique_codes}
                        resolved = mapped.map(code_to_name)
                        prefix_results.update(resolved)
                        # Remover já encontrados para não sobrepor com prefixos menores
                        nums = nums.drop(index=mapped.index)
                
                df.loc[mask_prefix, 'OPERADORA DO TELEFONE'] = prefix_results.fillna(df.loc[mask_prefix, 'OPERADORA DO TELEFONE'])

            # Limpeza final
            df['OPERADORA DO TELEFONE'] = df['OPERADORA DO TELEFONE'].fillna("NÃO CONSTA")
            df = df.drop(columns=['_clean_tel_enrich'])
            return df
        except Exception as e:
            import traceback
            print(f"Erro no filtro de operadora: {e}")
            traceback.print_exc()
            df['OPERADORA DO TELEFONE'] = "ERRO"
            return df

    def _get_ch_client(self):
        # Mock
        class MockResult:
            def __init__(self):
                self.result_rows = []
                self.column_names = []
        class MockCH:
            def query(self, q, p, settings=None):
                return MockResult()
        return MockCH()

    def _process_extraction_dataframe_fixed(self, tid, df, filters, workbook, sheet, header_fmt, header_written, start_row_count):
        """
        Sub-motor de processamento de dataframe para extração (VETORIZADO).
        Normaliza telefones, filtra operadoras e escreve no Excel com performance titanium.
        """
        if df.empty: return df

        # 1. Normalização de Telefones (Vetorizada)
        for col in ['DDD1', 'TEL1', 'DDD2', 'TEL2']:
            if col not in df.columns: df[col] = ""
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace(['nan', 'NaN', 'None', '<NA>'], '')

        # Limpeza e concatenação (T1)
        df['full_t1'] = (df['DDD1'] + df['TEL1']).str.replace(r'\D', '', regex=True)
        # Regra do 9º dígito (Vetorizada)
        mask10_t1 = (df['full_t1'].str.len() == 10) & (df['full_t1'].str[2].isin(['6','7','8','9']))
        df.loc[mask10_t1, 'full_t1'] = df['full_t1'].str[:2] + '9' + df['full_t1'].str[2:]
        
        # Limpeza e concatenação (T2)
        df['full_t2'] = (df['DDD2'] + df['TEL2']).str.replace(r'\D', '', regex=True)
        mask10_t2 = (df['full_t2'].str.len() == 10) & (df['full_t2'].str[2].isin(['6','7','8','9']))
        df.loc[mask10_t2, 'full_t2'] = df['full_t2'].str[:2] + '9' + df['full_t2'].str[2:]

        # Filtro de Junk (Zeros ou Vazios)
        def clean_junk(ser):
            # Transforma em vazio se for só zeros ou se após o DDD (2 primeiros dígitos) for só zeros
            is_all_zero = ser.str.replace('0', '') == ''
            is_local_zero = (ser.str.len() >= 2) & (ser.str.slice(2).str.replace('0', '') == '')
            return np.where(is_all_zero | is_local_zero, "", ser)
        
        df['full_t1'] = clean_junk(df['full_t1'])
        df['full_t2'] = clean_junk(df['full_t2'])

        # Identificação de Região (Pernambuco Fix)
        if filters.get("filtrar_ddd_regiao") and filters.get("uf"):
            # Mock de ddds
            valid_ddds = ['11', '12']
            df['is_reg1'] = df['DDD1'].astype(str).isin(valid_ddds)
            df['is_reg2'] = df['DDD2'].astype(str).isin(valid_ddds)
        else:
            df['is_reg1'] = True
            df['is_reg2'] = True

        # Identificação de Tipos (Vetorizada)
        def get_tipo_vec(col):
            # O TEL1/TEL2 original (já limpo de .0 e nan)
            clean = df[col].str.replace(r'\D', '', regex=True)
            is_cel = (clean.str.len() == 9) | ((clean.str.len() == 8) & (clean.str.slice(0,1).isin(['6','7','8','9'])))
            return np.where(clean.str.len() > 0, np.where(is_cel, "CELULAR", "FIXO"), None)

        df['t1_tipo'] = get_tipo_vec('TEL1')
        df['t2_tipo'] = get_tipo_vec('TEL2')

        tipo_req = filters.get("tipo_tel", "TODOS")
        if tipo_req == "AMBOS":
            mask = ((df['t1_tipo'] == "CELULAR") & (df['t2_tipo'] == "FIXO")) | ((df['t1_tipo'] == "FIXO") & (df['t2_tipo'] == "CELULAR"))
            df = df[mask].copy()
        elif tipo_req != "TODOS":
            df = df[(df['t1_tipo'] == tipo_req) | (df['t2_tipo'] == tipo_req)].copy()

        if df.empty: return df

        # Seleção do Telefone (Vetorizada com Filtro Regional)
        if tipo_req in ["CELULAR", "FIXO"]:
            # Só seleciona se for do tipo correto E (se filtro on) for da região correta
            mask1 = (df['t1_tipo'] == tipo_req) & (df['is_reg1']) & (df['full_t1'] != "")
            mask2 = (df['t2_tipo'] == tipo_req) & (df['is_reg2']) & (df['full_t2'] != "")
            df['TELEFONE SOLICITADO'] = np.where(mask1, df['full_t1'], 
                                        np.where(mask2, df['full_t2'], ""))
        elif tipo_req == "AMBOS":
            # Para AMBOS, mostramos os dois, mas filtrados por região se necessário
            t1_valid = (df['full_t1'] != "") & (df['is_reg1'])
            t2_valid = (df['full_t2'] != "") & (df['is_reg2'])
            t1_part = np.where(t1_valid, df['t1_tipo'].astype(str) + ": " + df['full_t1'], "")
            t2_part = np.where(t2_valid, df['t2_tipo'].astype(str) + ": " + df['full_t2'], "")
            df['TELEFONE SOLICITADO'] = t1_part + np.where((t1_part != "") & (t2_part != ""), " | ", "") + t2_part
        else: # TODOS
            c1_reg = (df['t1_tipo'] == "CELULAR") & (df['is_reg1']) & (df['full_t1'] != "")
            c2_reg = (df['t2_tipo'] == "CELULAR") & (df['is_reg2']) & (df['full_t2'] != "")
            f1_reg = (df['t1_tipo'] == "FIXO") & (df['is_reg1']) & (df['full_t1'] != "")
            f2_reg = (df['t2_tipo'] == "FIXO") & (df['is_reg2']) & (df['full_t2'] != "")
            
            df['TELEFONE SOLICITADO'] = np.where(c1_reg, df['full_t1'],
                                        np.where(c2_reg, df['full_t2'],
                                        np.where(f1_reg, df['full_t1'],
                                        np.where(f2_reg, df['full_t2'], ""))))
        
        # Se após a seleção o telefone estiver vazio e o usuário pediu filtragem ou somente com telefone, removemos a linha
        if filters.get("filtrar_ddd_regiao") or filters.get("somente_com_telefone"):
            df = df[df['TELEFONE SOLICITADO'] != ""].copy()
            if df.empty: return df
                                        
        # Drop de colunas auxiliares
        drop_cols = [c for c in ['DDD1', 'TEL1', 'DDD2', 'TEL2', 't1_tipo', 't2_tipo', 'full_t1', 'full_t2'] if c in df.columns]
        df = df.drop(columns=drop_cols)
        
        # Enriquecimento de Operadora (em lotes)
        df = self._append_operator_column(tid, df)

        # Filtros de Operadora (Vetorizados)
        op_inc = str(filters.get("operadora_inc", "TODAS")).upper()
        op_exc = str(filters.get("operadora_exc", "NENHUMA")).upper()
        
        if 'OPERADORA DO TELEFONE' in df.columns:
            if op_exc != "NENHUMA":
                pattern = "VIVO|TELEFONICA" if op_exc == "VIVO" else re.escape(op_exc)
                mask_exc = df['OPERADORA DO TELEFONE'].str.upper().str.contains(pattern, na=False, regex=True)
                df = df[~mask_exc]
                
            if op_inc != "TODAS":
                pattern = "VIVO|TELEFONICA" if op_inc == "VIVO" else re.escape(op_inc)
                mask_inc = df['OPERADORA DO TELEFONE'].str.upper().str.contains(pattern, na=False, regex=True)
                df = df[mask_inc]

        if df.empty: return df

        # Formatação Final (Paridade Total com o Print)
        df.columns = [str(c).upper().replace('_', ' ').strip() for c in df.columns]
        
        # Mapeamento para os nomes exatos do print
        final_mapping = {
            'NOME': 'NOME DA EMPRESA', 
            'SITUACAO': 'SITUACAO CADASTRAL', 
            'RUA': 'LOGRADOURO', 
            'NUMERO': 'NUMERO DA FAIXADA',
            'OPERADORA DO TELEFONE': 'OPERADORA DO TELEFONE' # Já está certo no df['OPERADORA DO TELEFONE']
        }
        df = df.rename(columns=final_mapping)
        
        sit_map = {'01':'NULA','02':'ATIVA','03':'SUSPENSA','04':'INAPTA','08':'BAIXADA'}
        if 'SITUACAO CADASTRAL' in df.columns:
            df['SITUACAO CADASTRAL'] = df['SITUACAO CADASTRAL'].astype(str).str.zfill(2).map(sit_map).fillna(df['SITUACAO CADASTRAL'])

        # Ordem Exata do Print
        final_columns = ['CNPJ', 'NOME DA EMPRESA', 'SITUACAO CADASTRAL', 'CNAE', 'LOGRADOURO', 'NUMERO DA FAIXADA']
        
        # Regra Regional (MT, MS, GO, DF) -> Adiciona COMPLEMENTO após NUMERO
        uf_req = str(filters.get("uf", "")).strip().upper()
        if uf_req in ["DF", "GO", "MT", "MS"]:
            final_columns.append('COMPLEMENTO')
            
        # Continuação da Ordem: BAIRRO, CIDADE, UF, CEP, TELEFONE SOLICITADO, OPERADORA DO TELEFONE
        final_columns.extend(['BAIRRO', 'CIDADE', 'UF', 'CEP', 'TELEFONE SOLICITADO', 'OPERADORA DO TELEFONE'])
        
        for c in final_columns:
            if c not in df.columns: df[c] = ""
            else: df[c] = df[c].astype(str).replace(['nan', 'NaN', 'None', '<NA>'], "")
        
        df_final = df[final_columns].fillna("")
        
        # Escrita no Excel ... (Preservada)
        return df_final

if __name__ == "__main__":
    cp = Checkpoint()
    # Test column mapping and logic
    # ...
