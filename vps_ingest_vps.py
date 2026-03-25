import subprocess
import os
import time
import sys

# Configuration
SHARE_TOKEN = "YggdBLfdninEJX9"
BASE_URL = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}/2026-03"
TARGET_DB = "hemn_update_tmp"
DOWNLOAD_DIR = "/var/www/hemn_cloud/downloads"
LOG_FILE = "/var/www/hemn_cloud/ingest_march_2026.log"

FILES = [
    "Cnaes.zip", "Motivos.zip", "Municipios.zip", "Naturezas.zip", "Paises.zip", "Qualificacoes.zip", "Simples.zip",
    "Empresas0.zip", "Empresas1.zip", "Empresas2.zip", "Empresas3.zip", "Empresas4.zip",
    "Empresas5.zip", "Empresas6.zip", "Empresas7.zip", "Empresas8.zip", "Empresas9.zip",
    "Socios0.zip", "Socios1.zip", "Socios2.zip", "Socios3.zip", "Socios4.zip",
    "Socios5.zip", "Socios6.zip", "Socios7.zip", "Socios8.zip", "Socios9.zip",
    "Estabelecimentos0.zip", "Estabelecimentos1.zip", "Estabelecimentos2.zip", "Estabelecimentos3.zip", "Estabelecimentos4.zip",
    "Estabelecimentos5.zip", "Estabelecimentos6.zip", "Estabelecimentos7.zip", "Estabelecimentos8.zip", "Estabelecimentos9.zip"
]

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")

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

def setup_db():
    log("Setting up database schema...")
    run_cmd(f'clickhouse-client -q "CREATE DATABASE IF NOT EXISTS {TARGET_DB}"')
    
    # Table schemas
    schemas = {
        "empresas": """
            cnpj_basico String, razao_social String, natureza_juridica String, qualificacao_responsavel String,
            porte_empresa String, ente_federativo_responsavel String, capital_social Float64
        """,
        "estabelecimento": """
            cnpj_basico String, cnpj_ordem String, cnpj_dv String, matriz_filial String,
            nome_fantasia String, situacao_cadastral String, data_situacao_cadastral String,
            motivo_situacao_cadastral String, nome_cidade_exterior String, pais String,
            data_inicio_atividades String, cnae_fiscal String, cnae_fiscal_secundaria String,
            tipo_logradouro String, logradouro String, numero String, complemento String,
            bairro String, cep String, uf String, municipio String, ddd1 String,
            telefone1 String, ddd2 String, telefone2 String, ddd_fax String, fax String,
            correio_eletronico String, situacao_especial String, data_situacao_especial String,
            cnpj String
        """,
        "socios": """
            cnpj String, cnpj_basico String, identificador_de_socio String, nome_socio String,
            cnpj_cpf_socio String, qualificacao_socio String, data_entrada_sociedade String,
            pais String, representante_legal String, nome_representante String,
            qualificacao_representante_legal String, faixa_etaria String, socio_chave String
        """,
        "municipio": "codigo String, descricao String",
        "paises": "codigo String, descricao String",
        "natureza_juridica": "codigo String, descricao String",
        "qualificacao_socio": "codigo String, descricao String",
        "cnae": "codigo String, descricao String",
        "motivo": "codigo String, descricao String",
        "simples": "cnpj_basico String, opcao_pelo_simples String, data_opcao_simples String, data_exclusao_simples String, opcao_mei String, data_opcao_mei String, data_exclusao_mei String"
    }
    
    for table, cols in schemas.items():
        engine = "MergeTree ORDER BY tuple()"
        if table == "empresas": engine = "MergeTree ORDER BY (razao_social, cnpj_basico)"
        elif table == "estabelecimento": engine = "MergeTree ORDER BY (cnpj, cnpj_basico, uf, municipio)"
        elif table == "socios": engine = "MergeTree ORDER BY (cnpj_cpf_socio, nome_socio, cnpj, cnpj_basico)"
        elif table == "municipio": engine = "MergeTree ORDER BY codigo"
        
        run_cmd(f'clickhouse-client -q "CREATE TABLE IF NOT EXISTS {TARGET_DB}.{table} ({cols}) ENGINE = {engine}"')

def get_table_for_file(filename):
    if "Empresas" in filename: return "empresas"
    if "Estabelecimentos" in filename: return "estabelecimento"
    if "Socios" in filename: return "socios"
    if "Municipios" in filename: return "municipio"
    if "Paises" in filename: return "paises"
    if "Naturezas" in filename: return "natureza_juridica"
    if "Qualificacoes" in filename: return "qualificacao_socio"
    if "Cnaes" in filename: return "cnae"
    if "Motivos" in filename: return "motivo"
    if "Simples" in filename: return "simples"
    return None

def process_file(filename):
    table = get_table_for_file(filename)
    if not table:
        log(f"Skipping unknown file type: {filename}")
        return
    
    # Resumable logic: Check if we've already tried this file in this log
    # (Simplified: just check if 'Finished <filename>' is in the log)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            if f"Finished {filename}" in f.read():
                log(f"Resuming: Skipping already finished {filename}")
                return

    zip_path = os.path.join(DOWNLOAD_DIR, filename)
    url = f"{BASE_URL}/{filename}"
    
    log(f"Starting {filename}...")
    
    # 1. Download
    success, _ = run_cmd(f'curl -u {SHARE_TOKEN}: -L -o {zip_path} "{url}"')
    if not success: return
    
    # 2. Ingest
    log(f"Ingesting into {table}...")
    if table == "estabelecimento":
        cols = "cnpj_basico,cnpj_ordem,cnpj_dv,matriz_filial,nome_fantasia,situacao_cadastral,data_situacao_cadastral,motivo_situacao_cadastral,nome_cidade_exterior,pais,data_inicio_atividades,cnae_fiscal,cnae_fiscal_secundaria,tipo_logradouro,logradouro,numero,complemento,bairro,cep,uf,municipio,ddd1,telefone1,ddd2,telefone2,ddd_fax,fax,correio_eletronico,situacao_especial,data_situacao_especial"
        # Calculate full CNPJ during insertion
        pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" --max_insert_block_size 100000 -q "INSERT INTO {TARGET_DB}.{table} ({cols}, cnpj) SELECT *, concat(cnpj_basico, cnpj_ordem, cnpj_dv) FROM input(\'{cols}\')"'
        run_cmd(pipe_cmd)
    elif table == "socios":
        cols = "cnpj_basico,identificador_de_socio,nome_socio,cnpj_cpf_socio,qualificacao_socio,data_entrada_sociedade,pais,representante_legal,nome_representante,qualificacao_representante_legal,faixa_etaria"
        pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" -q "INSERT INTO {TARGET_DB}.{table} ({cols}) FORMAT CSV"'
        run_cmd(pipe_cmd)
    else:
        # Standard CSV ingestion with semicolon delimiter
        pipe_cmd = f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" -q "INSERT INTO {TARGET_DB}.{table} FORMAT CSV"'
        run_cmd(pipe_cmd)
        
    # 3. Cleanup
    os.remove(zip_path)
    log(f"Finished {filename}")

if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    log("--- STARTING MARCH 2026 UPDATE ---")
    setup_db()
    
    for f in FILES:
        process_file(f)
        
    log("--- INGESTION COMPLETE ---")
    log("Next: Atomic swap and version update manually or via script.")
