#!/usr/bin/env python3
"""HEMN Cloud — Receita Federal monthly ingest (genérico, parametrizável).

Uso:
    python vps_generic_ingest.py --version "Maio/2026" --remote_month "2026-05"

O que faz:
  1. Cria/limpa schema em hemn_update_tmp (staging)
  2. Pra cada arquivo da Receita: download → unzip pipe → INSERT
  3. Atomic swap: EXCHANGE TABLES com hemn.<table> em loop
  4. Atualiza hemn._metadata.db_version
  5. Limpa flag /var/www/hemn_cloud/.receita_update_pending

Idempotente: se interrompido, releitura do log permite resume (skipa
arquivos já marcados como Finished).

Histórico:
  Reconstruído 2026-05-05 a partir do commit aef5508 (vps_ingest_vps.py).
  Diferenças vs original:
    - --version e --remote_month parametrizados (era hardcoded "2026-03")
    - Atomic swap incluído (faltava)
    - Update do _metadata incluído (faltava)
    - Limpa flag pending no fim
"""
import argparse
import os
import subprocess
import sys
import time

# === CONFIG ===
SHARE_TOKEN = "YggdBLfdninEJX9"
BASE_URL_PREFIX = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}"
TARGET_DB = "hemn_update_tmp"
PROD_DB = "hemn"
APP_DIR = "/var/www/hemn_cloud"
DOWNLOAD_DIR = os.path.join(APP_DIR, "downloads")
LOG_FILE = os.path.join(APP_DIR, "receita_cron.log")
PENDING_FLAG = os.path.join(APP_DIR, ".receita_update_pending")

FILES = [
    # Pequenos primeiro (lookup tables)
    "Cnaes.zip", "Motivos.zip", "Municipios.zip", "Naturezas.zip",
    "Paises.zip", "Qualificacoes.zip", "Simples.zip",
    # Empresas (10 partes)
    "Empresas0.zip", "Empresas1.zip", "Empresas2.zip", "Empresas3.zip", "Empresas4.zip",
    "Empresas5.zip", "Empresas6.zip", "Empresas7.zip", "Empresas8.zip", "Empresas9.zip",
    # Sócios (10 partes)
    "Socios0.zip", "Socios1.zip", "Socios2.zip", "Socios3.zip", "Socios4.zip",
    "Socios5.zip", "Socios6.zip", "Socios7.zip", "Socios8.zip", "Socios9.zip",
    # Estabelecimentos (10 partes — mais pesado, último)
    "Estabelecimentos0.zip", "Estabelecimentos1.zip", "Estabelecimentos2.zip",
    "Estabelecimentos3.zip", "Estabelecimentos4.zip", "Estabelecimentos5.zip",
    "Estabelecimentos6.zip", "Estabelecimentos7.zip", "Estabelecimentos8.zip",
    "Estabelecimentos9.zip",
]


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run_cmd(cmd, check=True):
    log(f"Running: {cmd}")
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        log(f"ERROR ({proc.returncode}): {proc.stderr.strip()[:500]}")
        if check:
            return False, proc.stderr
    return proc.returncode == 0, proc.stdout


def setup_db():
    log("Setting up temporary database schema...")
    run_cmd(f'clickhouse-client -q "CREATE DATABASE IF NOT EXISTS {TARGET_DB}"')

    schemas = {
        "empresas": ("""
            cnpj_basico String, razao_social String, natureza_juridica String,
            qualificacao_responsavel String, porte_empresa String,
            ente_federativo_responsavel String, capital_social Float64
        """, "MergeTree ORDER BY (razao_social, cnpj_basico)"),
        "estabelecimento": ("""
            cnpj_basico String, cnpj_ordem String, cnpj_dv String, matriz_filial String,
            nome_fantasia String, situacao_cadastral String, data_situacao_cadastral String,
            motivo_situacao_cadastral String, nome_cidade_exterior String, pais String,
            data_inicio_atividades String, cnae_fiscal String, cnae_fiscal_secundaria String,
            tipo_logradouro String, logradouro String, numero String, complemento String,
            bairro String, cep String, uf String, municipio String, ddd1 String,
            telefone1 String, ddd2 String, telefone2 String, ddd_fax String, fax String,
            correio_eletronico String, situacao_especial String, data_situacao_especial String,
            cnpj String
        """, "MergeTree ORDER BY (cnpj, cnpj_basico, uf, municipio)"),
        "socios": ("""
            cnpj String, cnpj_basico String, identificador_de_socio String, nome_socio String,
            cnpj_cpf_socio String, qualificacao_socio String, data_entrada_sociedade String,
            pais String, representante_legal String, nome_representante String,
            qualificacao_representante_legal String, faixa_etaria String, socio_chave String
        """, "MergeTree ORDER BY (cnpj_cpf_socio, nome_socio, cnpj, cnpj_basico)"),
        "municipio": ("codigo String, descricao String", "MergeTree ORDER BY codigo"),
        "paises": ("codigo String, descricao String", "MergeTree ORDER BY tuple()"),
        "natureza_juridica": ("codigo String, descricao String", "MergeTree ORDER BY tuple()"),
        "qualificacao_socio": ("codigo String, descricao String", "MergeTree ORDER BY tuple()"),
        "cnae": ("codigo String, descricao String", "MergeTree ORDER BY tuple()"),
        "motivo": ("codigo String, descricao String", "MergeTree ORDER BY tuple()"),
        "simples": ("""
            cnpj_basico String, opcao_pelo_simples String, data_opcao_simples String,
            data_exclusao_simples String, opcao_mei String, data_opcao_mei String,
            data_exclusao_mei String
        """, "MergeTree ORDER BY tuple()"),
    }

    for table, (cols, engine) in schemas.items():
        run_cmd(f'clickhouse-client -q "CREATE TABLE IF NOT EXISTS {TARGET_DB}.{table} ({cols}) ENGINE = {engine}"')
        run_cmd(f'clickhouse-client -q "TRUNCATE TABLE {TARGET_DB}.{table}"')


def get_table_for_file(filename):
    f = filename.lower()
    if "empresas" in f: return "empresas"
    if "estabelecimentos" in f: return "estabelecimento"
    if "socios" in f: return "socios"
    if "municipios" in f: return "municipio"
    if "paises" in f: return "paises"
    if "naturezas" in f: return "natureza_juridica"
    if "qualificacoes" in f: return "qualificacao_socio"
    if "cnaes" in f: return "cnae"
    if "motivos" in f: return "motivo"
    if "simples" in f: return "simples"
    return None


def already_finished(filename, version):
    """Verifica no log se esse file já foi finalizado nesta versão (resume)."""
    if not os.path.exists(LOG_FILE):
        return False
    marker = f"Finished {filename} for {version}"
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            return marker in f.read()
    except Exception:
        return False


def process_file(filename, remote_month, version):
    table = get_table_for_file(filename)
    if not table:
        log(f"Skipping unknown file type: {filename}")
        return True

    if already_finished(filename, version):
        log(f"Resuming: Skipping already finished {filename} (version {version})")
        return True

    zip_path = os.path.join(DOWNLOAD_DIR, filename)
    url = f"{BASE_URL_PREFIX}/{remote_month}/{filename}"

    log(f"Processing {filename}...")

    # 1) Download
    ok, _ = run_cmd(f'curl -u {SHARE_TOKEN}: -L -s -o {zip_path} "{url}"')
    if not ok or not os.path.exists(zip_path) or os.path.getsize(zip_path) < 100:
        log(f"FAILED download {filename}")
        return False

    # 2) Ingest via unzip pipe
    log(f"Ingesting into {TARGET_DB}.{table}...")
    if table == "estabelecimento":
        cols = ("cnpj_basico,cnpj_ordem,cnpj_dv,matriz_filial,nome_fantasia,"
                "situacao_cadastral,data_situacao_cadastral,motivo_situacao_cadastral,"
                "nome_cidade_exterior,pais,data_inicio_atividades,cnae_fiscal,"
                "cnae_fiscal_secundaria,tipo_logradouro,logradouro,numero,complemento,"
                "bairro,cep,uf,municipio,ddd1,telefone1,ddd2,telefone2,ddd_fax,fax,"
                "correio_eletronico,situacao_especial,data_situacao_especial")
        cols_typed = " String, ".join(cols.split(",")) + " String"
        pipe = (f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" '
                f'--max_insert_block_size 100000 --input_format_allow_errors_num 1000 '
                f'--input_format_allow_errors_ratio 0.05 -q '
                f'"INSERT INTO {TARGET_DB}.{table} ({cols},cnpj) '
                f'SELECT *, concat(cnpj_basico, cnpj_ordem, cnpj_dv) FROM input(\'{cols_typed}\') '
                f'FORMAT CSV"')
    elif table == "socios":
        cols = ("cnpj_basico,identificador_de_socio,nome_socio,cnpj_cpf_socio,"
                "qualificacao_socio,data_entrada_sociedade,pais,representante_legal,"
                "nome_representante,qualificacao_representante_legal,faixa_etaria")
        pipe = (f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" '
                f'--input_format_allow_errors_num 1000 --input_format_allow_errors_ratio 0.05 '
                f'-q "INSERT INTO {TARGET_DB}.{table} ({cols}) FORMAT CSV"')
    else:
        pipe = (f'unzip -p {zip_path} | clickhouse-client --format_csv_delimiter ";" '
                f'--input_format_allow_errors_num 1000 --input_format_allow_errors_ratio 0.05 '
                f'-q "INSERT INTO {TARGET_DB}.{table} FORMAT CSV"')

    ok, _ = run_cmd(pipe)
    if not ok:
        log(f"FAILED ingest {filename}")
        return False

    # 3) Cleanup
    try:
        os.remove(zip_path)
    except Exception:
        pass
    log(f"Finished {filename} for {version}")
    return True


# Tabelas que devem ser swapadas (ignora _metadata)
SWAP_TABLES = ["cnae", "motivo", "municipio", "natureza_juridica", "paises",
               "qualificacao_socio", "simples", "empresas", "estabelecimento", "socios"]


def atomic_swap(version):
    """EXCHANGE TABLES de cada tabela do staging com produção. Falha em uma = aborta antes de qualquer swap."""
    log(f"--- Atomic swap: {TARGET_DB} <-> {PROD_DB} ---")

    # Pre-check: todas as tabelas têm dados não-zero?
    for t in SWAP_TABLES:
        ok, out = run_cmd(f'clickhouse-client -q "SELECT count() FROM {TARGET_DB}.{t}"', check=False)
        if not ok:
            log(f"ABORT swap: {TARGET_DB}.{t} sem schema")
            return False
        n = int((out or "0").strip() or 0)
        if n == 0:
            log(f"ABORT swap: {TARGET_DB}.{t} esta vazio (n={n})")
            return False
        log(f"  {TARGET_DB}.{t}: {n:,} linhas")

    # Faz swap em sequência. Se falhar no meio, não tem como reverter trivialmente —
    # mas ClickHouse EXCHANGE TABLES é atômico individualmente.
    for t in SWAP_TABLES:
        ok, _ = run_cmd(f'clickhouse-client -q "EXCHANGE TABLES {TARGET_DB}.{t} AND {PROD_DB}.{t}"')
        if not ok:
            log(f"CRITICAL: swap falhou em {t}. Estado pode estar inconsistente!")
            return False
        log(f"  swapped {t}")

    # Atualiza _metadata.db_version
    run_cmd(f'clickhouse-client -q "ALTER TABLE {PROD_DB}._metadata UPDATE value = \'{version}\' WHERE key = \'db_version\'"')
    log(f"_metadata.db_version atualizado para {version}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="Ex: Maio/2026")
    parser.add_argument("--remote_month", required=True, help="Pasta na Receita: 2026-05")
    parser.add_argument("--task_id", default=None, help="Identificador opcional pra log")
    parser.add_argument("--skip_setup", action="store_true", help="Não recriar schema (resume)")
    parser.add_argument("--skip_swap", action="store_true", help="Só ingere; não faz swap")
    args = parser.parse_args()

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Sanity: unzip e clickhouse-client disponíveis?
    for tool in ("unzip", "clickhouse-client", "curl"):
        if subprocess.run(f"which {tool}", shell=True, capture_output=True).returncode != 0:
            log(f"CRITICAL: {tool} nao instalado")
            return 1

    log(f"--- STARTING GENERIC UPDATE FOR {args.version} ({args.remote_month}) ---")
    if args.task_id:
        log(f"task_id={args.task_id}")

    if not args.skip_setup:
        setup_db()

    failed = []
    for f in FILES:
        if not process_file(f, args.remote_month, args.version):
            failed.append(f)
            log(f"CRITICAL ERROR: Failed at {f}. Aborting.")
            return 1

    if failed:
        log(f"Falhou em {len(failed)} arquivos: {failed}")
        return 1

    log("--- INGESTION COMPLETE ---")

    if args.skip_swap:
        log("--skip_swap especificado; nao fez swap nem atualizou metadata.")
        return 0

    if not atomic_swap(args.version):
        log("CRITICAL: swap falhou — base em estado possivelmente inconsistente.")
        return 1

    # Limpa flag de update pendente
    if os.path.exists(PENDING_FLAG):
        try:
            os.remove(PENDING_FLAG)
            log("Flag pending removido.")
        except Exception:
            pass

    log(f"=== UPDATE TO {args.version} COMPLETE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
