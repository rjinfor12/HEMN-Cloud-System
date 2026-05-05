#!/usr/bin/env python3
"""HEMN Cloud — Receita Federal monthly check orchestrator.

Roda diariamente via cron (00:00). Detecta a versão mais recente publicada
pela Receita Federal no share público e compara com o que tá ativo no
ClickHouse (`hemn._metadata.db_version`).

Comportamento:
  - Se versões iguais → loga "up to date" e sai.
  - Se versão remota mais nova → loga ALERTA e cria flag-file em
    `/var/www/hemn_cloud/.receita_update_pending`. NÃO dispara ingestão
    automática por padrão (controlada por AUTO_INGEST abaixo).
  - Se AUTO_INGEST=True E flag detectado, chama vps_generic_ingest.py.

Histórico:
  2026-04-14: versão original criada como vps_check_receita_updates.py
              (commit aef5508), evoluiu pra vps_receita_orchestrator.py
              que auto-disparava o ingest.
  2026-04-27: ambos scripts removidos do servidor (não-commitados).
              Cron rodava todo dia falhando "No such file".
  2026-05-05: reconstruído deste commit baseado no histórico do log.
              AUTO_INGEST default=False (mais seguro; usuário ativa depois
              de validar o ingest pra Maio/2026).
"""
import os
import re
import sys
import time
import subprocess
import urllib.request
import urllib.error
import base64
from datetime import datetime

# === CONFIG ===
SHARE_TOKEN = "YggdBLfdninEJX9"
BASE_URL = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}"
PROBE_FILE = "Cnaes.zip"  # arquivo pequeno só pra testar disponibilidade
APP_DIR = "/var/www/hemn_cloud"
LOG_PATH = os.path.join(APP_DIR, "receita_cron.log")
PENDING_FLAG = os.path.join(APP_DIR, ".receita_update_pending")
INGEST_SCRIPT = os.path.join(APP_DIR, "vps_generic_ingest.py")
PYTHON_BIN = os.path.join(APP_DIR, "venv/bin/python")

# Se True, dispara o ingest como subprocess quando detectar update.
# Default False por segurança: ingest demora horas e qualquer bug pode
# corromper a base. Ative SOMENTE depois de testar o ingest manualmente.
AUTO_INGEST = False

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def probe_month(year, month):
    """Tenta GET /YYYY-MM/Cnaes.zip. Retorna True se 200/206/HEAD-only OK."""
    url = f"{BASE_URL}/{year:04d}-{month:02d}/{PROBE_FILE}"
    auth = base64.b64encode(f"{SHARE_TOKEN}:".encode()).decode()
    req = urllib.request.Request(url, method="HEAD", headers={
        "Authorization": f"Basic {auth}",
        "User-Agent": "HEMN-orchestrator/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status in (200, 206)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        log(f"WARN probing {year:04d}-{month:02d}: HTTP {e.code}")
        return False
    except Exception as e:
        log(f"WARN probing {year:04d}-{month:02d}: {e}")
        return False


def detect_remote_version():
    """Procura pra trás a partir do mês corrente até achar o mais recente disponível.
    Retorna (version_str, year, month) ou (None, None, None).
    """
    now = datetime.now()
    # Tenta o mês corrente, mês anterior, antepassado, etc. (até 4 meses atrás)
    for delta in range(0, 5):
        y, m = now.year, now.month - delta
        while m <= 0:
            m += 12
            y -= 1
        log(f"Probing {BASE_URL}/{y:04d}-{m:02d}/{PROBE_FILE}...")
        if probe_month(y, m):
            version = f"{MESES_PT[m]}/{y}"
            log(f"Detected remote version: {version} in folder {y:04d}-{m:02d}")
            return version, y, m
    return None, None, None


def get_local_version():
    """Le hemn._metadata.db_version via clickhouse-client (lógica simples, sem dep externa)."""
    try:
        out = subprocess.check_output([
            "clickhouse-client",
            "--query=SELECT value FROM hemn._metadata WHERE key = 'db_version' LIMIT 1 FORMAT TabSeparated"
        ], stderr=subprocess.STDOUT, timeout=15).decode().strip()
        return out or None
    except subprocess.CalledProcessError as e:
        log(f"WARN reading local version: {e.output.decode(errors='replace').strip()}")
        return None
    except Exception as e:
        log(f"WARN reading local version: {e}")
        return None


def trigger_ingest(version, year, month):
    """Dispara vps_generic_ingest.py como subprocess se AUTO_INGEST=True."""
    remote_month = f"{year:04d}-{month:02d}"
    if not os.path.exists(INGEST_SCRIPT):
        log(f"CRITICAL: {INGEST_SCRIPT} nao existe — nao posso disparar ingest")
        return False
    cmd = [PYTHON_BIN, INGEST_SCRIPT, "--version", version, "--remote_month", remote_month]
    log(f"Executing: {' '.join(cmd)}")
    try:
        # Não captura output (deixa fluir pro log do cron)
        result = subprocess.run(cmd, timeout=8 * 3600)  # 8h max
        if result.returncode != 0:
            log(f"CRITICAL ERROR: Ingestion script failed with exit code {result.returncode}")
            return False
        log(f"Ingestion script returned 0 (success)")
        return True
    except subprocess.TimeoutExpired:
        log("CRITICAL ERROR: Ingestion exceeded 8h timeout")
        return False
    except Exception as e:
        log(f"CRITICAL ERROR running ingest: {e}")
        return False


def main():
    log("=== STARTING RECEITA UPDATE CHECK ===")
    remote_version, y, m = detect_remote_version()
    if not remote_version:
        log("CRITICAL: nao consegui detectar versao remota (Receita Federal nao respondeu).")
        return 2

    local_version = get_local_version() or "Desconhecida"
    log(f"Version Check -> Local: {local_version} | Remote: {remote_version}")

    if remote_version == local_version:
        log(f"System is up to date ({local_version}). No action needed.")
        # Limpa flag se houver
        if os.path.exists(PENDING_FLAG):
            os.remove(PENDING_FLAG)
        return 0

    # Versões diferentes: criar flag e logar alerta visível
    log(f"!!! UPDATE AVAILABLE !!! Local={local_version} | Remote={remote_version}")
    log(f"Folder: {y:04d}-{m:02d}")
    try:
        with open(PENDING_FLAG, "w", encoding="utf-8") as f:
            f.write(f"{remote_version}\n{y:04d}-{m:02d}\n{datetime.now().isoformat()}\n")
        log(f"Flag criado em {PENDING_FLAG}")
    except Exception as e:
        log(f"WARN writing flag: {e}")

    if AUTO_INGEST:
        log("AUTO_INGEST=True -> Triggering ingestion...")
        ok = trigger_ingest(remote_version, y, m)
        return 0 if ok else 1
    else:
        log("AUTO_INGEST=False -> Update detected but ingestion NOT triggered automatically.")
        log(f"Para rodar manualmente: {PYTHON_BIN} {INGEST_SCRIPT} --version '{remote_version}' --remote_month '{y:04d}-{m:02d}'")
        return 0


if __name__ == "__main__":
    sys.exit(main())
