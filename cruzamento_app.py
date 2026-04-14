import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import pandas as pd
import unidecode
import re

import time
from datetime import datetime
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DE UFs COM LÓGICA COMPLETA
# ─────────────────────────────────────────────
SMART_UFS    = {'GO', 'DF', 'MT', 'MS'}
PREFIXES     = r'\b(RUA|R|AV|AVEN|AVENIDA|PRACA|PCO|PC|RODOVIA|ROD|TRV|TRAVESSA|ALAMEDA|EST|ESTRADA|VL|VILA|BC|BECO|GALERIA|Q|QUADRA)\b'
MACRO_REGEX  = r'\b(Q|QD|QUADRA|L|LT|LOTE|KM|BR|ROD|RODOVIA)\b'

# Dark Studio Colors
BG    = "#18181b"   # Base dark (Zinc 900)
CARD  = "#27272a"   # Sidebar / Panel (Zinc 800)
ACCENT= "#2563eb"   # Technical Blue (Blue 600)
TEXT  = "#f4f4f5"   # Off-white (Zinc 50)
SUB   = "#a1a1aa"   # Muted text (Zinc 400)
DARK  = "#09090b"   # Console black (Zinc 950)

# ─────────────────────────────────────────────
# FUNÇÕES DE NORMALIZAÇÃO
# ─────────────────────────────────────────────
def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).upper()
    text = unidecode.unidecode(text)
    text = re.sub(r'[^A-Z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def normalize_street(street):
    norm = normalize_text(street)
    return re.sub(r'^' + PREFIXES + r'\s+', '', norm).strip()

def clean_num_str(num):
    if pd.isna(num): return ""
    s = str(num).strip().upper()
    if s.endswith('.0'): s = s[:-2]
    return s

def normalize_number(num):
    s_num = str(num).strip().split('.')[0]
    n = re.sub(r'[^A-Z0-9]', '', s_num.upper())
    if n.isdigit(): return str(int(n)) # Remove zeros à esquerda (05 -> 5)
    return n

def normalize_cep(cep):
    if pd.isna(cep): return ""
    # Trata caso de 4190040.0 -> 4190040 e depois zfill(8) -> 04190040
    s_cep = str(cep).strip().split('.')[0]
    c = re.sub(r'[^0-9]', '', s_cep)
    if not c: return ""
    return c.zfill(8)

def is_cep_geral(cep_norm):
    """CEP geral = cobre localidade/bairro inteiro → últimos 3 dígitos são '000'."""
    return len(cep_norm) == 8 and cep_norm.endswith('000')

# ─────────────────────────────────────────────
# MARGEM DE PROXIMIDADE (TALVEZ)
# ─────────────────────────────────────────────
def check_proximity(c_num_raw, c_comp_raw, v_raw):
    """
    Se falhou no SIM exato, avalia se está na margem de ±20 (Número) ou ±5 (Lote).
    """
    c_full = f"{str(c_num_raw).strip()} {str(c_comp_raw).strip()}".upper()
    v_full = str(v_raw).upper()

    # 1. Extração de Quadra e Lote
    def get_ql(text):
        q = re.search(r'\b(?:Q|QD|QUADRA)\s*(\d+)\b', text)
        l = re.search(r'\b(?:L|LT|LOTE)\s*(\d+)\b', text)
        if q and l: return int(q.group(1)), int(l.group(1))
        return None, None

    c_q, c_l = get_ql(c_full)
    v_q, v_l = get_ql(v_full)

    # Regra Quadra/Lote: Apenas se ambar tiverem a marcação de Quadra e Lote
    if (c_q is not None) and (v_q is not None):
        if c_q == v_q and abs(c_l - v_l) <= 5:
            return True
        return False

    # 2. Regra de Número Puro com Paridade Estrita
    c_digs = re.findall(r'\d+', str(c_num_raw))
    v_digs = re.findall(r'\d+', str(v_raw))

    if c_digs and v_digs:
        try:
            cn = int(c_digs[0])
            vn = int(v_digs[0])
            # Se for ano numérico bizarro no lugar errado, limita a valores prováveis
            if cn < 100000 and vn < 100000:
                # Regra de Paridade (Ambos pares ou ambos ímpares):
                if (cn % 2) == (vn % 2):
                    if abs(cn - vn) <= 40: # Margem de 40 números = 20 residências
                        return True
        except ValueError:
            pass
    return False


# ─────────────────────────────────────────────
# LÓGICA SMART (GO, DF, MT, MS)
# Regras:
#   1. Match exato: num+comp normalizado bate com v_norm → SIM
#   2. S/N no CNPJ: só aceita se v_raw também for S/N e sem comp Macro
#   3. Dígito primário do CNPJ DEVE bater com o dígito primário do Vivo
#   4. Complemento MACRO (Quadra/Lote/KM) → verificar se está contido na string Vivo
#   5. Complemento MICRO (Sala/Apto/Casa) → ignorar, basta o número bater
# ─────────────────────────────────────────────
def is_number_match_smart(c_num_raw, c_comp_raw, v_raw, v_norm):
    # Normalizar entradas
    c_num_str  = str(c_num_raw).strip() if pd.notna(c_num_raw) else ""
    c_comp_str = str(c_comp_raw).strip().upper() if pd.notna(c_comp_raw) else ""
    c_num_norm = normalize_number(c_num_str)

    # ── Regra 1: Match exato combinado (num + comp) ──
    if c_comp_str:
        c_combined_norm = normalize_number(c_num_str + " " + c_comp_str)
        if c_combined_norm and c_combined_norm == v_norm:
            return True

    # ── Regra 2: Tratar S/N ──
    is_c_sn = (not c_num_norm) or c_num_norm in ('SN', 'S', '0', '00')
    is_v_sn = (not v_norm)     or v_norm in ('SN', 'S', '0', '00')
    if is_c_sn:
        # S/N no CNPJ só bate com S/N na Vivo, sem complemento Macro pendente
        has_macro_comp = bool(c_comp_str and re.search(MACRO_REGEX, c_comp_str))
        return is_v_sn and not has_macro_comp

    # ── Regra 3: Dígito primário DEVE ser igual ──
    c_digits = re.findall(r'\d+', c_num_str)
    v_digits = re.findall(r'\d+', v_raw)
    if not c_digits or not v_digits:
        return False
    if c_digits[0] != v_digits[0]:
        return False   # número base diferente → descarta imediatamente

    # ── Regra 4 / 5: Analisar complemento ──
    if not c_comp_str:
        # Sem complemento → basta o número base bater (Micro implícito)
        return True

    is_macro = bool(re.search(MACRO_REGEX, c_comp_str))

    if is_macro:
        # Complemento MACRO: precisa aparecer na string Vivo bruta
        comp_norm = normalize_number(c_comp_str)
        return comp_norm in v_norm
    else:
        # Complemento MICRO (Sala, Apto, Casa…) → ignorar, número base já bateu
        return True

# ─────────────────────────────────────────────
# CARREGAMENTO VIVO (MÚLTIPLOS ARQUIVOS + MULTI-ABAS)
# ─────────────────────────────────────────────
def load_vivo(paths, log_fn):
    all_dfs = []
    for path in paths:
        xl = pd.ExcelFile(path)
        sheets = xl.sheet_names
        log_fn(f"  📂 {os.path.basename(path)} → {len(sheets)} aba(s)")
        for sh in sheets:
            df = xl.parse(sh)
            log_fn(f"      ↳ Aba '{sh}': {len(df):,} linhas")
            all_dfs.append(df)
    df_vivo = pd.concat(all_dfs, ignore_index=True)
    log_fn(f"  ✅ Total Vivo carregada: {len(df_vivo):,} linhas")
    return df_vivo

# ─────────────────────────────────────────────
# CARREGAMENTO CNPJ (MÚLTIPLAS ABAS)
# ─────────────────────────────────────────────
def load_cnpj(path, log_fn):
    xl = pd.ExcelFile(path)
    sheets = xl.sheet_names
    log_fn(f"  📂 {os.path.basename(path)} → {len(sheets)} aba(s)")
    all_dfs = []
    for sh in sheets:
        df = xl.parse(sh)
        log_fn(f"      ↳ Aba '{sh}': {len(df):,} linhas")
        all_dfs.append(df)
    df_cnpj = pd.concat(all_dfs, ignore_index=True)
    log_fn(f"  ✅ Total CNPJ carregado: {len(df_cnpj):,} linhas")
    return df_cnpj

# ─────────────────────────────────────────────
# MOTOR DE CRUZAMENTO
# ─────────────────────────────────────────────
def run_match(cnpj_path, vivo_paths, tipo_filtro, log_fn, progress_fn, done_fn, cancel_event):
    try:
        start_total = time.time()
        log_fn("=" * 58)
        log_fn(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando cruzamento...")
        log_fn(f"  CNPJ:  {os.path.basename(cnpj_path)}")
        log_fn(f"  Vivo:  {len(vivo_paths)} arquivo(s) selecionado(s)")
        log_fn(f"  Filtro Tipo: {tipo_filtro}")
        log_fn("  Regra: CEP EXATO + Paridade Estrita + Margem 40 (20 Residências)")
        log_fn("=" * 58)

        log_fn(f"\n[{datetime.now().strftime('%H:%M:%S')}] Carregando CNPJ...")
        df_cnpj = load_cnpj(cnpj_path, log_fn)
        if cancel_event.is_set(): done_fn(None, 0, 0, cancelled=True); return

        log_fn(f"\n[{datetime.now().strftime('%H:%M:%S')}] Carregando Cobertura Vivo...")
        df_vivo = load_vivo(vivo_paths, log_fn)
        if cancel_event.is_set(): done_fn(None, 0, 0, cancelled=True); return

        # Detectar colunas CNPJ
        city_col  = next((c for c in df_cnpj.columns if 'CIDADE' in c.upper() or 'MUNIC' in c.upper()), None)
        street_col= next((c for c in df_cnpj.columns if 'LOGRADOURO' in c.upper() or 'ENDER' in c.upper()), None)
        num_col   = next((c for c in df_cnpj.columns if 'NUMERO' in c.upper() or 'NÚMERO' in c.upper()), None)
        # Detectar complemento com nomes variados: COMPLEMENTO, COMPL, COMP_LOGRADOURO, etc.
        comp_col  = next((c for c in df_cnpj.columns if 'COMPLEMENT' in c.upper()), None)
        if comp_col is None:
            comp_col = next((c for c in df_cnpj.columns
                             if c.strip().upper() in ('COMPL', 'COMP', 'COMPLEMENTO_LOGRADOURO',
                                                      'COMP_LOGRADOURO', 'COMPL_LOGRADOURO')), None)
        uf_col    = next((c for c in df_cnpj.columns if c.strip().upper() == 'UF'), None)
        cep_col_c = next((c for c in df_cnpj.columns if 'CEP' in c.upper()), None)

        if comp_col is None:
            log_fn("  ⚠️  ATENÇÃO: Coluna de COMPLEMENTO não detectada. Endereços S/N com Quadra/Lote serão tratados como SEM COBERTURA (modo conservador).")

        # Detectar colunas Vivo
        v_city_col  = next((c for c in df_vivo.columns if 'CIDADE' in c.upper()), None)
        v_street_col= next((c for c in df_vivo.columns if 'LOGRADOURO' in c.upper()), None)
        v_num_col   = next((c for c in df_vivo.columns if c.strip().upper() in ('NUM','NUMERO','NÚMERO')), None)
        v_cep_col   = next((c for c in df_vivo.columns if 'CEP' in c.upper()), None)
        v_tipo_col  = next((c for c in df_vivo.columns if c.strip().upper() == 'TIPO'), None)

        log_fn(f"\n  Colunas CNPJ → Cidade:{city_col} | Rua:{street_col} | Num:{num_col} | Comp:{comp_col} | UF:{uf_col} | CEP:{cep_col_c}")
        log_fn(f"  Colunas Vivo → Cidade:{v_city_col} | Rua:{v_street_col} | Num:{v_num_col} | CEP:{v_cep_col} | Tipo:{v_tipo_col}\n")

        # Filtrar por TIPO (Flexível: HORIZONTAL/VERTICAL)
        if tipo_filtro != "TODOS":
            if v_tipo_col:
                initial_count = len(df_vivo)
                search_val = tipo_filtro[:7].upper() # Captura 'HORIZON' ou 'VERTICA'
                df_vivo = df_vivo[df_vivo[v_tipo_col].astype(str).str.upper().str.contains(search_val)]
                final_count = len(df_vivo)
                log_fn(f"  > Filtro aplicado: TIPO contém '{search_val}'.")
                log_fn(f"  > Linhas na base Vivo: {initial_count:,} → {final_count:,}")
            else:
                log_fn(f"  ⚠️ Coluna 'TIPO' não encontrada na base Vivo. O filtro '{tipo_filtro}' será ignorado.")

        if cancel_event.is_set(): done_fn(None, 0, 0, cancelled=True); return
        if len(df_vivo) == 0:
            log_fn(f"\n❌ ERRO: Nenhuma linha da Vivo sobrou após o filtro '{tipo_filtro}'.")
            done_fn(None, 0, 0, cancelled=False)
            return

        if 'cobertura' in df_cnpj.columns:
            df_cnpj.drop(columns=['cobertura'], inplace=True)

        # Normalizar Vivo
        log_fn(f"[{datetime.now().strftime('%H:%M:%S')}] Indexando base Vivo por CEP...")
        df_vivo['_NORM_NUM']    = df_vivo[v_num_col].apply(normalize_number) if v_num_col else ""
        df_vivo['_CLEAN_NUM']   = df_vivo[v_num_col].apply(clean_num_str) if v_num_col else ""
        df_vivo['_NORM_CEP']    = df_vivo[v_cep_col].apply(normalize_cep) if v_cep_col else ""
        df_vivo['_NORM_STREET'] = df_vivo[v_street_col].apply(normalize_street) if v_street_col else ""

        vivo_cep_dict = {}
        for cep, rn, nn, st in zip(df_vivo['_NORM_CEP'], df_vivo['_CLEAN_NUM'],
                                    df_vivo['_NORM_NUM'], df_vivo['_NORM_STREET']):
            if not cep: continue
            if cep not in vivo_cep_dict: vivo_cep_dict[cep] = []
            vivo_cep_dict[cep].append({'raw': rn, 'norm': nn, 'street': st})

        log_fn(f"[{datetime.now().strftime('%H:%M:%S')}] Base Vivo indexada ({len(vivo_cep_dict):,} CEPs únicos).")
        
        # Amostragem para depuração
        sample_ceps = list(vivo_cep_dict.keys())[:3]
        log_fn(f"  🔍 Amostra CEPs Vivo Indexados: {sample_ceps}")
        log_fn(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando cruzamento de {len(df_cnpj):,} empresas...\n")

        df_cnpj = df_cnpj.reset_index(drop=True)
        total = len(df_cnpj)
        cobertura_results = {}
        match_count = 0
        talvez_count = 0
        start_time  = time.time()

        for row_idx, row in df_cnpj.iterrows():
            # ── Checar cancelamento a cada iteração ──
            if cancel_event.is_set():
                log_fn(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🛑 Cancelado pelo usuário em {row_idx:,}/{total:,}.")
                done_fn(None, 0, 0, cancelled=True)
                return

            if row_idx % 10000 == 0 and row_idx > 0:
                elapsed = time.time() - start_time
                pct  = row_idx / total * 100
                rate = row_idx / elapsed if elapsed > 0 else 1
                eta  = (total - row_idx) / rate if rate > 0 else 0
                log_fn(f"[{datetime.now().strftime('%H:%M:%S')}] {row_idx:,}/{total:,} ({pct:.1f}%) | SIM: {match_count:,} | TALVEZ: {talvez_count:,} | ETA: ~{eta/60:.1f} min")
                progress_fn(pct)

            uf_val    = normalize_text(row.get(uf_col, '') if uf_col else '')
            use_smart = uf_val in SMART_UFS
            cnpj_num  = row.get(num_col, '') if num_col else ''
            cnpj_comp = row.get(comp_col, '') if comp_col else None
            cnpj_cep  = normalize_cep(row.get(cep_col_c, '') if cep_col_c else '')
            cnpj_num_n= normalize_number(cnpj_num)
            cnpj_street_n = normalize_street(row.get(street_col, '') if street_col else '')
            matched   = False

            if not cnpj_cep:
                cobertura_results[row_idx] = 'NÃO'
                continue

            vivo_entries = vivo_cep_dict.get(cnpj_cep, [])
            if not vivo_entries:
                cobertura_results[row_idx] = 'NÃO'
                continue

            # ── Regra: CEP Geral → pré-filtrar por logradouro ──
            # CEP geral (termina em 000) cobre bairro inteiro → CEP sozinho não discrimina
            # Filtramos as entradas Vivo que têm o mesmo logradouro antes de checar o número
            if is_cep_geral(cnpj_cep) and cnpj_street_n and v_street_col:
                street_filtered = [vd for vd in vivo_entries if vd['street'] == cnpj_street_n]
                # Se houver entradas com o logradouro → usa apenas elas
                # Se não houver nenhuma → sem cobertura (logradouro não está na Vivo)
                vivo_entries = street_filtered
                if not vivo_entries:
                    cobertura_results[row_idx] = 'NÃO'
                    continue

            # ── Modo conservador: S/N sem complemento detectado ──
            if use_smart and comp_col is None:
                is_sn = (not cnpj_num_n) or cnpj_num_n in ('SN', 'S', '0', '00')
                if is_sn:
                    cobertura_results[row_idx] = 'NÃO'
                    continue

            match_status = 'NÃO'

            for vd in vivo_entries:
                is_sim = False
                if use_smart:
                    is_sim = is_number_match_smart(cnpj_num, cnpj_comp, vd['raw'], vd['norm'])
                else:
                    is_sim = (cnpj_num_n and cnpj_num_n == vd['norm'])

                if is_sim:
                    match_status = 'SIM'
                    break  # Encontrou o SIM, encerra a busca para este CNPJ

                # Se não é SIM, checamos proximidade. Se der TALVEZ, continuamos a busca
                # pois ainda podemos encontrar um SIM mais pra frente na lista da Vivo.
                if match_status == 'NÃO':
                    if check_proximity(cnpj_num, cnpj_comp, vd['raw']):
                        match_status = 'TALVEZ'

            cobertura_results[row_idx] = match_status
            if match_status == 'SIM': 
                match_count += 1
            elif match_status == 'TALVEZ':
                talvez_count += 1

        df_cnpj['cobertura'] = df_cnpj.index.map(cobertura_results)
        elapsed = time.time() - start_total
        log_fn(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ Concluído em {elapsed/60:.1f} min!")
        nao_count = total - match_count - talvez_count
        log_fn(f"  SIM: {match_count:,}  |  TALVEZ: {talvez_count:,}  |  NÃO: {nao_count:,}")
        log_fn(f"\nPronto! Clique em \"💾 Salvar Arquivo\" para escolher onde salvar.")
        progress_fn(100)
        done_fn(df_cnpj, match_count, total, cancelled=False)

    except Exception as e:
        import traceback
        log_fn(f"\n❌ ERRO: {e}\n{traceback.format_exc()}")
        done_fn(None, 0, 0, cancelled=False)


# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cruzamento de Cobertura Vivo")
        self.geometry("900x750")
        self.minsize(850, 720)
        self.configure(fg_color=BG)
        self.vivo_files   = []
        self.cnpj_path    = tk.StringVar()
        self.tipo_filtro  = tk.StringVar(value="TODOS")
        self.running      = False
        self._result_df   = None
        self.export_filter = tk.StringVar(value="TODOS")
        self._cancel_event = threading.Event()  # sinal de cancelamento
        self._build_ui()

    def _build_ui(self):
        # Configurar malha para layout Dashboard (Duas Colunas)
        self.grid_columnconfigure(1, weight=1)  # Area principal expande
        self.grid_rowconfigure(0, weight=1)     # Altura total

        # ── 1. SIDEBAR OESTE (Configurações) ──
        sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=CARD)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1) # Spacer push buttons down

        # Header Title
        ctk.CTkLabel(sidebar, text="Cruzamento CNPJ × Vivo", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=TEXT).grid(row=0, column=0, padx=20, pady=(25, 2), sticky="w")
        ctk.CTkLabel(sidebar, text="Motor Geográfico v2.0", font=ctk.CTkFont(family="Consolas", size=11), text_color=SUB).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        # Config: Base CNPJ
        ctk.CTkLabel(sidebar, text="BASE PRINCIPAL (CNPJ)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=SUB).grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        
        cnpj_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        cnpj_frame.grid(row=3, column=0, padx=20, sticky="ew")
        
        self.cnpj_entry = ctk.CTkEntry(cnpj_frame, textvariable=self.cnpj_path, fg_color=DARK, text_color=TEXT, border_color="#3f3f46", border_width=1, corner_radius=4, height=32)
        self.cnpj_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.cnpj_entry.configure(state="disabled")
        
        ctk.CTkButton(cnpj_frame, text="...", command=self._pick_cnpj, fg_color="#3f3f46", hover_color="#52525b", text_color=TEXT, font=ctk.CTkFont(weight="bold"), width=36, height=32, corner_radius=4).pack(side="right")

        # Config: Bases Vivo
        ref_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        ref_frame.grid(row=4, column=0, padx=20, pady=(25, 5), sticky="ew")
        
        ctk.CTkLabel(ref_frame, text="REFERÊNCIA DE COBERTURA", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=SUB).pack(side="left")
        
        # Filtro TIPO Compacto na mesma linha
        self.combo_tipo = ctk.CTkOptionMenu(ref_frame, variable=self.tipo_filtro, values=["TODOS", "HORIZONTAL", "VERTICAL"], fg_color=DARK, button_color="#3f3f46", button_hover_color="#52525b", dropdown_fg_color=DARK, dropdown_hover_color="#3f3f46", text_color=TEXT, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), height=24, width=100)
        self.combo_tipo.pack(side="right")
        
        btn_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        btn_box.grid(row=5, column=0, padx=20, sticky="ew", pady=(0, 6))
        ctk.CTkButton(btn_box, text="+ Adicionar Base", command=self._add_vivo, fg_color="#3f3f46", hover_color="#52525b", text_color=TEXT, font=ctk.CTkFont(family="Segoe UI", size=12), height=28).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_box, text="✕ Limpar", command=self._clear_vivo, fg_color="transparent", border_width=1, border_color="#7f1d1d", hover_color="#450a0a", text_color="#ef4444", font=ctk.CTkFont(family="Segoe UI", size=12), height=28, width=70).pack(side="right")

        # Scrollable Frame listando Vivo Files
        self.vivo_list_frame = ctk.CTkScrollableFrame(sidebar, fg_color=DARK, border_color="#3f3f46", border_width=1, corner_radius=4, height=120)
        self.vivo_list_frame.grid(row=6, column=0, padx=20, sticky="ew")
        self.vivo_labels = [] # Lista de UIs dos arquivos selecionados
        
        self.vivo_count_label = ctk.CTkLabel(sidebar, text="0 bases carregadas.", font=ctk.CTkFont(family="Consolas", size=11), text_color=SUB)
        self.vivo_count_label.grid(row=7, column=0, padx=20, pady=(4, 0), sticky="w")

        # Footer Actions
        self.btn_start = ctk.CTkButton(sidebar, text="▶ START ENGINE", command=self._start, fg_color=ACCENT, hover_color="#1d4ed8", text_color="white", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), height=42, corner_radius=4)
        self.btn_start.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.btn_cancel = ctk.CTkButton(sidebar, text="⬛ STOP ENGINE", command=self._cancel, fg_color="#ef4444", hover_color="#dc2626", text_color="white", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), height=42, corner_radius=4)
        self.btn_cancel.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.btn_cancel.grid_remove()

        # Filtro de Exportação (Nova Opção)
        ctk.CTkLabel(sidebar, text="FILTRAR EXPORTAÇÃO", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=SUB).grid(row=11, column=0, padx=20, pady=(15, 2), sticky="w")
        self.combo_export = ctk.CTkOptionMenu(sidebar, variable=self.export_filter, values=["TODOS", "SIM", "TALVEZ", "NÃO"], fg_color=DARK, button_color="#3f3f46", button_hover_color="#52525b", dropdown_fg_color=DARK, dropdown_hover_color="#3f3f46", text_color=TEXT, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), height=36)
        self.combo_export.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.btn_save = ctk.CTkButton(sidebar, text="💾 EXPORT RESULT", command=self._save_file, fg_color="#18181b", border_width=1, border_color="#3f3f46", hover_color="#27272a", text_color=SUB, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), height=42, corner_radius=4, state="disabled")
        self.btn_save.grid(row=13, column=0, padx=20, pady=(0, 25), sticky="ew")


        # ── 2. MAIN AREA LESTE (Monitor/Log) ──
        monitor = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        monitor.grid(row=0, column=1, sticky="nsew")
        monitor.grid_columnconfigure(0, weight=1)
        monitor.grid_rowconfigure(1, weight=1) # O terminal expande

        # Header Técnico
        header = ctk.CTkFrame(monitor, fg_color=DARK, height=44, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        
        self.status_indicator = ctk.CTkLabel(header, text="● STANDBY", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#a1a1aa")
        self.status_indicator.grid(row=0, column=0, padx=20, pady=10)
        
        rules_text = "MODO SMART: GO/DF/MT/MS  |  MODO SIMPLES: Demais UFs"
        ctk.CTkLabel(header, text=rules_text, font=ctk.CTkFont(family="Consolas", size=11), text_color=SUB).grid(row=0, column=1, padx=20, sticky="e")

        # Terminal Realístico
        self.log_box = ctk.CTkTextbox(monitor, fg_color=DARK, text_color=TEXT, corner_radius=0, border_spacing=10, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.log_box.configure(state="disabled")

        # Barra de Progresso Envolvente
        progress_bar_box = ctk.CTkFrame(monitor, fg_color="transparent")
        progress_bar_box.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        progress_bar_box.grid_columnconfigure(0, weight=1)

        self.pct_label = ctk.CTkLabel(progress_bar_box, text="Aguardando dados da Base CNPJ...", font=ctk.CTkFont(family="Consolas", size=11), text_color=SUB)
        self.pct_label.grid(row=0, column=0, sticky="w", pady=(0,4))

        self.progress = ctk.CTkProgressBar(progress_bar_box, progress_color=ACCENT, fg_color=CARD, height=4, corner_radius=0)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew")

    # ── Ações ──
    def _pick_cnpj(self):
        p = filedialog.askopenfilename(title="Selecionar planilha CNPJ",
                                        filetypes=[("Excel", "*.xlsx *.xls")])
        if p:
            self.cnpj_entry.configure(state="normal")
            self.cnpj_entry.delete(0, "end")
            self.cnpj_entry.insert(0, os.path.basename(p))
            self.cnpj_entry.configure(state="disabled")
            self.cnpj_path.set(p)

    def _add_vivo(self):
        paths = filedialog.askopenfilenames(title="Selecionar planilha(s) Cobertura Vivo",
                                             filetypes=[("Excel", "*.xlsx *.xls")])
        for p in paths:
            if p not in self.vivo_files:
                self.vivo_files.append(p)
                lbl = ctk.CTkLabel(self.vivo_list_frame, text="📄 " + os.path.basename(p), font=ctk.CTkFont(family="Consolas", size=11), text_color=TEXT, anchor="w")
                lbl.pack(fill="x", pady=2)
                self.vivo_labels.append(lbl)
        self._update_vivo_label()

    def _clear_vivo(self):
        self.vivo_files.clear()
        for lbl in self.vivo_labels: 
            lbl.destroy()
        self.vivo_labels.clear()
        self._update_vivo_label()

    def _update_vivo_label(self):
        n = len(self.vivo_files)
        if n > 0:
            self.vivo_count_label.configure(text=f"{n} bases", text_color=TEXT)
        else:
            self.vivo_count_label.configure(text="0 bases", text_color=SUB)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_progress(self, pct):
        self.progress.set(pct / 100) # CTkProgressBar aceita valor de 0 a 1
        self.pct_label.configure(text=f"{pct:.1f}%")
        self.update_idletasks()

    def _start(self):
        if self.running: return
        cnpj = self.cnpj_path.get().strip()
        if not cnpj or not os.path.exists(cnpj):
            messagebox.showerror("Erro", "Selecione a planilha CNPJ válida."); return
        if not self.vivo_files:
            messagebox.showerror("Erro", "Adicione ao menos uma planilha de Cobertura Vivo."); return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.progress.set(0)
        self.pct_label.configure(text="")
        self.running = True
        self._cancel_event.clear()
        
        self.btn_cancel.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew") # Correção crucial: usar grid em vez de pack
        
        self.btn_start.configure(state="disabled", text="▶ PROCESSING...", fg_color=CARD)
        self.btn_save.configure(state="disabled", fg_color="#18181b", text_color=SUB, border_color="#3f3f46")
        self.status_indicator.configure(text="● RUNNING", text_color="#10b981")

        threading.Thread(
            target=run_match,
            args=(cnpj, list(self.vivo_files), self.tipo_filtro.get(), self._log, self._set_progress, self._on_done, self._cancel_event),
            daemon=True
        ).start()

    def _cancel(self):
        if not self.running: return
        self.btn_cancel.configure(state="disabled", text="⬛ STOPPING...")
        self._log("\nSolicitando cancelamento... Aguarde encerrar a operação atual.")
        self._cancel_event.set()

    def _on_done(self, df_result, match_count, total, cancelled=False):
        self.running = False
        
        self.btn_cancel.grid_remove() # Oculta cancelar
        self.btn_cancel.configure(state="normal", text="⬛ STOP ENGINE")
        
        self.btn_start.configure(state="normal", text="▶ START ENGINE", fg_color=ACCENT)
        self.status_indicator.configure(text="● STANDBY", text_color="#a1a1aa")
        
        if cancelled:
            self.pct_label.configure(text="Cruzamento cancelado.")
            return

        if df_result is not None:
            self._result_df = df_result
            self.btn_save.configure(state="normal", fg_color="#18181b", text_color="#10b981", border_color="#10b981")
        else:
            messagebox.showerror("Erro", "Ocorreu um erro. Verifique o log.")

    def _reset(self):
        """Zera tudo para um novo cruzamento."""
        self.cnpj_path.set("")
        self.cnpj_entry.configure(state="normal")
        self.cnpj_entry.delete(0, "end")
        self.cnpj_entry.configure(state="disabled")
        
        self._clear_vivo()
        
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.progress.set(0)
        self.pct_label.configure(text="Aguardando dados da Base CNPJ...")
        
        self.btn_start.configure(state="normal", text="▶ START ENGINE", fg_color=ACCENT)
        self.btn_save.configure(state="disabled", fg_color="#18181b", text_color=SUB, border_color="#3f3f46")
        self._result_df = None

    def _save_file(self):
        if self._result_df is None:
            return
            
        # Aplicar filtro de exportação se não for "TODOS"
        filter_val = self.export_filter.get()
        df_to_save = self._result_df.copy()
        
        name_suffix = ""
        if filter_val != "TODOS":
            df_to_save = df_to_save[df_to_save['cobertura'] == filter_val]
            name_suffix = f"_SOMENTE_{filter_val.replace('Ã', 'A')}"
            
        if len(df_to_save) == 0:
            messagebox.showwarning("Aviso", f"Nenhum registro encontrado para o filtro '{filter_val}'.")
            return

        # Sugerir nome baseado na planilha CNPJ selecionada
        cnpj_base = os.path.splitext(os.path.basename(self.cnpj_path.get()))[0] if self.cnpj_path.get() else "CNPJ"
        sugestao  = f"{cnpj_base}_COBERTURA_VIVO{name_suffix}.xlsx"
        out_path  = filedialog.asksaveasfilename(
            title="Salvar resultado como...",
            initialfile=sugestao,
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return  # Usuário cancelou

        self.btn_save.configure(state="disabled", text="💾 EXPORTING...", fg_color="#18181b", text_color=SUB, border_color="#3f3f46")
        self.btn_start.configure(state="disabled")
        df_to_save = self._result_df

        def _write():
            try:
                # 1. Limpeza de caracteres ilegais que corrompem o XML do Excel
                # (Caracteres de controle ASCII 0-31, exceto tab, nl, cr)
                def clean_illegal_chars(val):
                    if isinstance(val, str):
                        return "".join(c for c in val if c.isprintable() or c in "\t\n\r")
                    return val
                
                df_clean = df_to_save.applymap(clean_illegal_chars)
                
                max_rows = 900000  # Reduzido de 1M para 900k para maior segurança
                total_rows = len(df_clean)
                
                # Tentar usar xlsxwriter (mais estável para arquivos gigantes), fallback para openpyxl
                engine_to_use = 'xlsxwriter'
                try:
                    import xlsxwriter
                except ImportError:
                    engine_to_use = 'openpyxl'

                if total_rows <= max_rows:
                    df_clean.to_excel(out_path, index=False, engine=engine_to_use)
                else:
                    with pd.ExcelWriter(out_path, engine=engine_to_use) as writer:
                        for i in range(0, total_rows, max_rows):
                            chunk = df_clean.iloc[i : i + max_rows]
                            sheet_idx = (i // max_rows) + 1
                            chunk.to_excel(writer, sheet_name=f"Resultados_{sheet_idx}", index=False)
                            
                self.after(0, lambda: _on_save_ok(out_path))
            except PermissionError:
                self.after(0, lambda: _on_save_err(
                    f"Não foi possível salvar.\n\nVerifique se o arquivo '{os.path.basename(out_path)}' está aberto no Excel e feche-o antes de salvar.",
                    permission=True
                ))
            except Exception as e:
                self.after(0, lambda err=e: _on_save_err(str(err)))
                self.after(0, lambda err=e: _on_save_err(str(err)))

        def _on_save_ok(path):
            messagebox.showinfo("Salvo! 💾", f"Arquivo salvo em:\n{path}")
            ans = messagebox.askyesno("Abrir pasta?", "Deseja abrir a pasta onde o arquivo foi salvo?")
            if ans:
                os.startfile(os.path.dirname(path))
            # ── Reset completo para novo cruzamento ──
            self._reset()

        def _on_save_err(msg, permission=False):
            self.btn_save.configure(state="normal", text="💾 EXPORT RESULT", text_color="#10b981", border_color="#10b981")
            self.btn_start.configure(state="normal")
            messagebox.showerror("Erro ao salvar", msg)

        threading.Thread(target=_write, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
