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

print('=== INSPECAO DO EXCEL NO LADO DO SERVIDOR ===')
# Script para rodar no servidor vps
py_code = """
import pandas as pd
import os
path = '/var/www/hemn_cloud/storage/results/Extracao_9c2025e0.xlsx'
if os.path.exists(path):
    df = pd.read_excel(path, nrows=10)
    print(df.to_string())
else:
    print('Arquivo nao encontrado')
"""

# Escapa aspas para o comando bash
py_code_escaped = py_code.replace('"', '\\"').replace('\n', '; ')
print(run(f"/var/www/hemn_cloud/venv/bin/python -c \"{py_code_escaped}\""))

client.close()
