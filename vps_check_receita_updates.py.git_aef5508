import os
import requests
import re
from datetime import datetime
try:
    import clickhouse_connect
except ImportError:
    pass

# Configurações
SHARE_TOKEN = "YggdBLfdninEJX9"
BASE_URL = f"https://arquivos.receitafederal.gov.br/public.php/dav/files/{SHARE_TOKEN}/"
LOG_PATH = "/var/www/hemn_cloud/receita_update_monitor.log"

def get_current_db_version():
    """Lê a versão ativa do Clickhouse"""
    try:
        client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
        res = client.query("SELECT value FROM hemn._metadata WHERE key = 'db_version' LIMIT 1")
        if res.result_rows:
            return res.result_rows[0][0]
    except Exception as e:
        print(f"Error reading ClickHouse version: {e}")
    return "Desconhecida"

def check_remote_version():
    """Verifica a data dos arquivos no servidor da Receita"""
    try:
        response = requests.get(BASE_URL, timeout=15)
        if response.status_code != 200:
            return None
        
        # Procura por padrões de data na página (ex: 2026-04 ou datas de modificação)
        # Mais simples: Procura por arquivos .zip e pega a última data de modificação
        content = response.text
        # Regex para encontrar datas comuns no list de diretório Apache/Nginx
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', content)
        if dates:
            # Pega a data mais recente
            latest_date = max(dates)
            dt = datetime.strptime(latest_date, "%Y-%m-%d")
            return dt.strftime("%B/%Y").capitalize() # Ex: Abril/2026
    except Exception as e:
        print(f"Error checking remote version: {e}")
    return None

def notify_update(new_version):
    """Loga o alerta ou cria uma tarefa virtual na UI"""
    msg = f"[{datetime.now()}] ALERTA: Nova base da Receita disponível: {new_version}"
    print(msg)
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")
    
    # Criar uma 'tarefa' estática no SQLite para aparecer no painel
    # (Opcional, se o CloudEngine ler esta tabela)
    return True

def run_monitor():
    print(f"[{datetime.now()}] Iniciando monitoramento de versão...")
    current = get_current_db_version()
    remote = check_remote_version()
    
    if remote and remote not in current:
        print(f"Divergência detectada! Local: {current} | Remota (Geralmente): {remote}")
        notify_update(remote)
    else:
        print(f"Sistema atualizado. Local: {current}")

if __name__ == "__main__":
    run_monitor()
