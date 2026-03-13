import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print('=== INSPECAO DO EXCEL NO LADO DO SERVIDOR (CORRIGIDO) ===')
script = """
import pandas as pd
import os
import sys

path = '/var/www/hemn_cloud/storage/results/Extracao_9c2025e0.xlsx'
if not os.path.exists(path):
    print('Arquivo nao encontrado')
    sys.exit(0)

try:
    df = pd.read_excel(path, nrows=5)
    print('Colunas encontradas:', df.columns.tolist())
    print('\\nPrimeiras linhas:')
    print(df.to_string())
except Exception as e:
    print('Erro ao ler excel:', str(e))
"""

# Usando heredoc para evitar problemas de escape
client.exec_command("cat << 'EOF' > /tmp/inspect_excel.py\n" + script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/inspect_excel.py"))

client.close()
