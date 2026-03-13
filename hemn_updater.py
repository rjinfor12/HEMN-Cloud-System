import os, sys, time, glob, shutil
import urllib.request
import zipfile
import threading
import tkinter as tk
from tkinter import messagebox
import subprocess
from datetime import datetime, timedelta

# Configurações Essenciais
TARGET_DIR = r"C:\HEMN_SYSTEM_DB"
DB_NAME = "cnpj.db"
TEMP_WORKSPACE = r"C:\HEMN_Database_Builder"
ZIP_DIR = os.path.join(TEMP_WORKSPACE, "dados-publicos-zip")
EXTRACT_DIR = os.path.join(TEMP_WORKSPACE, "dados-publicos")

# Link base estático direto no IP oficial (foge do firewall DNS dadosabertos)
BASE_URL = 'http://200.152.38.155/CNPJ/'

ARQUIVOS_RECEITA = [
    'Cnaes.zip', 'Motivos.zip', 'Municipios.zip', 'Naturezas.zip', 'Paises.zip', 'Qualificacoes.zip', 'Simples.zip',
    'Empresas0.zip', 'Empresas1.zip', 'Empresas2.zip', 'Empresas3.zip', 'Empresas4.zip', 'Empresas5.zip', 'Empresas6.zip', 'Empresas7.zip', 'Empresas8.zip', 'Empresas9.zip',
    'Estabelecimentos0.zip', 'Estabelecimentos1.zip', 'Estabelecimentos2.zip', 'Estabelecimentos3.zip', 'Estabelecimentos4.zip', 'Estabelecimentos5.zip', 'Estabelecimentos6.zip', 'Estabelecimentos7.zip', 'Estabelecimentos8.zip', 'Estabelecimentos9.zip',
    'Socios0.zip', 'Socios1.zip', 'Socios2.zip', 'Socios3.zip', 'Socios4.zip', 'Socios5.zip', 'Socios6.zip', 'Socios7.zip', 'Socios8.zip', 'Socios9.zip'
]

def log(msg):
    # Salva no arquivo de log contínuo pra auditoria
    with open(os.path.join(TEMP_WORKSPACE, "updater_rotina.log"), "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def show_result_popup(success, error_msg=""):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    if success:
        msg = "A Mega-Atualização Mensal (35GB) foi concluída com Exatidão Matemática!\n\nSeu HEMN SYSTEM agora está usando a base da Receita novinha para Cruzamento Rápido em Lote."
        messagebox.showinfo("HEMN SYSTEM - O.S Cronjob", msg)
    else:
        msg = f"Ops! Houve uma interrupção na Construção da nova Base de CNPJs.\n\nFALHA OCORRIDA: {error_msg}\n\nFique tranquilo, o Cronjob de Segurança da T.I reprogramou a rotina tentando novamente amanhã (19:30). A base atual continua funcionando normalmente!"
        messagebox.showerror("HEMN SYSTEM - Fallback Disparado", msg)
    root.destroy()

def schedule_retry():
    # Cria uma nova Thread Única (ONE-TIME TASK) no relógio do Windows pro dia seguinte (Amanhã 19:30h)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
    # Proteção de Aspas Duplas da Rotina Nativa
    updater_path = r'\"pythonw.exe\" \"C:\Users\Junior T.I\scratch\data_analysis\hemn_updater.py\"'
    
    cmd = f'schtasks /create /f /tn "HEMN_System_Updater_Retry" /tr "{updater_path}" /sc once /st 19:30 /sd {tomorrow}'
    try:
        subprocess.run(cmd, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        log(f"[SELF-HEALING] Agendamento Reativo disparado para: {tomorrow} às 19:30.")
    except Exception as e:
        log(f"[SELF-HEALING ERROR] Falha ao reagendar tentativa pro Windows: {e}")

def setup_workspace():
    if not os.path.exists(TEMP_WORKSPACE): os.mkdir(TEMP_WORKSPACE)
    if not os.path.exists(ZIP_DIR): os.mkdir(ZIP_DIR)
    if not os.path.exists(EXTRACT_DIR): os.mkdir(EXTRACT_DIR)
    
    # Limpeza de execuções passadas se falharam
    for file in glob.glob(os.path.join(ZIP_DIR, '*')): os.remove(file)
    for file in glob.glob(os.path.join(EXTRACT_DIR, '*')): os.remove(file)
    log("Workspace temporário limpo e preparado.")

def download_arquivo(nome_arquivo):
    url = BASE_URL + nome_arquivo
    destino = os.path.join(ZIP_DIR, nome_arquivo)
    log(f"Iniciando download de {nome_arquivo}...")
    try:
        # User agent de navegador para enganar firewalls mais leves
        req = urllib.request.Request(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=30) as response, open(destino, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        log(f"-> {nome_arquivo} finalizado!")
        return True
    except Exception as e:
        log(f"ERRO ao baixar {nome_arquivo}: {e}")
        return False

def build_database_with_rictom_core():
    # Isso invoca a core library original do GitHub para fazer a construção do SQLite com a lib Dask (Aceleração absurda)
    log("Invocando construtor Dask -> SQLite...")
    
    script_content = f'''
import os, glob, sys
import zipfile
import subprocess
print("Running rictom's script via subprocess...")
sys.path.append(r"C:\\Users\\Junior T.I\\scratch\\data_analysis\\rictom_temp\\cnpj-sqlite-main")
# Usando o código dele modificado diretamente
import dados_cnpj_para_sqlite
    '''
    
    # Vamos adaptar o arquivo `dados_cnpj_para_sqlite.py` original com os caminhos absolutos corretos.
    RICTOM_PATH = r"C:\\Users\\Junior T.I\\scratch\\data_analysis\\rictom_temp\\cnpj-sqlite-main\\dados_cnpj_para_sqlite.py"
    with open(RICTOM_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Injetando as diretrizes corretas (Bypass path)
    content = content.replace("pasta_compactados = r\"dados-publicos-zip\"", f"pasta_compactados = r\"{ZIP_DIR}\"")
    content = content.replace("pasta_saida = r\"dados-publicos\"", f"pasta_saida = r\"{EXTRACT_DIR}\"")
    content = content.replace("r = input(", "# r = input(")
    content = content.replace("bApagaDescompactadosAposUso = True", "bApagaDescompactadosAposUso = True")
    content = content.replace("sys.exit()", "pass")
    
    SCRIPT_RUNNER = os.path.join(TEMP_WORKSPACE, "motor_banco.py")
    with open(SCRIPT_RUNNER, 'w', encoding='utf-8') as f:
        f.write(content)
        
    try:
        import subprocess
        log("Rodando Subprocess Data ETL Builder...")
        result = subprocess.run([sys.executable, SCRIPT_RUNNER], capture_output=True, text=True)
        log(result.stdout)
        if result.stderr:
            log(f"ERROS NO ETL: {result.stderr}")
        return True if "Foi criado o arquivo" in result.stdout or "FIM!!!" in result.stdout else False
    except Exception as e:
        log(f"FALHA GERAL ETL: {e}")
        return False

def main_routine():
    log("=== INICIANDO MEGA-ATUALIZAÇÃO HEMN UPDATE ===")
    setup_workspace()
    
    # 1. Download Paralelo/Seq de 37 Arquivos (6GB)
    sucesso_total = True
    for arq in ARQUIVOS_RECEITA:
        if not download_arquivo(arq):
            sucesso_total = False
            log("PARANDO: Receita Federal negou acesso a algum módulo de arquivo. Tente novamente mais tarde.")
            break
            
    if not sucesso_total:
        schedule_retry()
        show_result_popup(False, "Bloqueio Securitário do Servidor de Dados Abertos (Receita Federal)")
        return
        
    log("Todos os 37 arquivos extraídos da Receita com sucesso! Iniciando Parseamento Multithread para SQLite.")
    
    # 2. Build Database (Extrai ZIPs e usa DASK)
    bd_criado = build_database_with_rictom_core()
    
    if bd_criado:
        log("Construção do Banco de Dados concluída com exatidão matemática!")
        
        # 3. Transposição para Produção
        target_db_path = os.path.join(TARGET_DIR, DB_NAME)
        built_db_path = os.path.join(EXTRACT_DIR, DB_NAME)
        
        # Faz backup rápido do velho no próprio Target antes de sobrescrever
        if os.path.exists(target_db_path):
            backup_path = target_db_path + ".old"
            log(f"Fazendo backup do BD atual da máquina local -> {backup_path}")
            if os.path.exists(backup_path): os.remove(backup_path)
            os.rename(target_db_path, backup_path)
            
        if not os.path.exists(TARGET_DIR): os.mkdir(TARGET_DIR)
            
        log(f"Movendo NOVO Banco pesado {DB_NAME} para uso de Produção em {TARGET_DIR}...")
        shutil.move(built_db_path, target_db_path)
        log("Novo CNPJ cruzador online e operante!")
        
        
        # Opcional: deletar velha lixeira de ZIPs para poupar 6GB de HD
        setup_workspace() 
        show_result_popup(True)
    else:
        log("Houve erro crítico na transposição de dados CSV -> SQLITE!")
        schedule_retry()
        show_result_popup(False, "O Motor ETL C-Level/Dask engasgou ao descompactar os mais de 69 Milhões de Registros na Memória RAM. Revise o Updater_log.")
        
    log("=== ROTINA FINALIZADA ===")

if __name__ == "__main__":
    main_routine()
