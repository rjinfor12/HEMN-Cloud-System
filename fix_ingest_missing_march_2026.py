import subprocess
import os
import time
import sys
import sqlite3

# Configuration
SHARE_TOKEN = "YggdBLfdninEJX9"
BASE_URL = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}/2026-03"
TARGET_DB = "hemn_update_tmp"
DOWNLOAD_DIR = "/var/www/hemn_cloud/downloads"
LOG_FILE = "/var/www/hemn_cloud/ingest_march_2026_fix.log"
SQLITE_DB = "/var/www/hemn_cloud/hemn_cloud.db"
TASK_ID = "db_update_march_2026"

FILES_EMPRESA = [f"Empresas{i}.zip" for i in range(10)]
FILES_ESTAB = [f"Estabelecimentos{i}.zip" for i in range(10)]
ALL_FILES = FILES_EMPRESA + FILES_ESTAB

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")

def update_dashboard(progress, message, status="RUNNING"):
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        # Ensure task exists
        cursor.execute("INSERT OR IGNORE INTO background_tasks (id, username, module, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (TASK_ID, "admin", "DATABASE_UPDATE", status, 0.0, "Iniciando atualização...", time.strftime("%Y-%m-%d %H:%M:%S")))
        cursor.execute("UPDATE background_tasks SET progress = ?, message = ?, status = ? WHERE id = ?",
                       (progress, message, status, TASK_ID))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"Warning: Failed to update dashboard: {e}")

def run_cmd(cmd):
    log(f"Running: {cmd}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_bin, stderr_bin = process.communicate()
    stdout = stdout_bin.decode('utf-8', errors='replace')
    stderr = stderr_bin.decode('utf-8', errors='replace')
    if process.returncode != 0:
        log(f"ERROR: {stderr.strip()}")
        return False, stderr
    return True, stdout

def check_count(table):
    success, out = run_cmd(f'clickhouse-client -q "SELECT count() FROM {TARGET_DB}.{table}"')
    if success:
        return int(out.strip())
    return 0

def process_file(filename, idx, total):
    zip_path = os.path.join(DOWNLOAD_DIR, filename)
    url = f"{BASE_URL}/{filename}"
    
    table = "empresas" if "Empresas" in filename else "estabelecimento"
    progress = (idx / total) * 100
    msg = f"Processando {filename} ({idx}/{total})"
    log(msg)
    update_dashboard(progress, msg)

    # 1. Download
    success, _ = run_cmd(f'curl -u {SHARE_TOKEN}: -s -L -o {zip_path} "{url}"')
    if not success:
        update_dashboard(progress, f"Erro no download de {filename}", "FAILED")
        return False

    # 2. Ingest
    log(f"Ingesting into {table}...")
    prev_count = check_count(table)
    
    if table == "estabelecimento":
        # Explicit types and order for Estabelecimento (30 columns in CSV)
        cols_def = """
            cnpj_basico String, cnpj_ordem String, cnpj_dv String, matriz_filial String,
            nome_fantasia String, situacao_cadastral String, data_situacao_cadastral String,
            motivo_situacao_cadastral String, nome_cidade_exterior String, pais String,
            data_inicio_atividades String, cnae_fiscal String, cnae_fiscal_secundaria String,
            tipo_logradouro String, logradouro String, numero String, complemento String,
            bairro String, cep String, uf String, municipio String, ddd1 String,
            telefone1 String, ddd2 String, telefone2 String, ddd_fax String, fax String,
            correio_eletronico String, situacao_especial String, data_situacao_especial String
        """
        raw_cols = "cnpj_basico,cnpj_ordem,cnpj_dv,matriz_filial,nome_fantasia,situacao_cadastral,data_situacao_cadastral,motivo_situacao_cadastral,nome_cidade_exterior,pais,data_inicio_atividades,cnae_fiscal,cnae_fiscal_secundaria,tipo_logradouro,logradouro,numero,complemento,bairro,cep,uf,municipio,ddd1,telefone1,ddd2,telefone2,ddd_fax,fax,correio_eletronico,situacao_especial,data_situacao_especial"
        
        pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" -q "INSERT INTO {TARGET_DB}.{table} ({raw_cols}, cnpj) SELECT *, concat(cnpj_basico, cnpj_ordem, cnpj_dv) FROM input(\'{cols_def}\')"'
        run_cmd(pipe_cmd)
        
    else: # empresas
        # Corrected order: capital_social is index 4 in RFB CSV
        table_cols = "cnpj_basico,razao_social,natureza_juridica,qualificacao_responsavel,capital_social,porte_empresa,ente_federativo_responsavel"
        pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" -q "INSERT INTO {TARGET_DB}.{table} ({table_cols}) FORMAT CSV"'
        run_cmd(pipe_cmd)

    # 3. Verify
    new_count = check_count(table)
    if new_count <= prev_count:
        log(f"CRITICAL ERROR: No rows added from {filename}")
        update_dashboard(progress, f"Erro: {filename} resultou em 0 linhas", "FAILED")
        return False

    # 4. Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
    log(f"Finished {filename}")
    return True

if __name__ == "__main__":
    log("--- STARTING MARCH 2026 FIX (Empresas & Estabelecimentos) ---")
    update_dashboard(0, "Iniciando reprocessamento de tabelas críticas...")
    
    # Wipe empty tables first to be clean
    run_cmd(f'clickhouse-client -q "TRUNCATE TABLE {TARGET_DB}.empresas"')
    run_cmd(f'clickhouse-client -q "TRUNCATE TABLE {TARGET_DB}.estabelecimento"')

    total = len(ALL_FILES)
    for i, f in enumerate(ALL_FILES, 1):
        if not process_file(f, i, total):
            log("ABORTING due to error.")
            sys.exit(1)
            
    update_dashboard(100, "Atualização de base concluída com sucesso!", "COMPLETED")
    log("--- FIX COMPLETE ---")
