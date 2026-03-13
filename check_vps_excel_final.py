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

print('=== LENDO O EXCEL GERADO (72be2375) ===')
file_path = '/var/www/hemn_cloud/storage/results/Extracao_72be2375.xlsx'

check_script = f"""
import pandas as pd
import os

path = '{file_path}'
if not os.path.exists(path):
    print(f"ERRO: Arquivo {{path}} nao existe.")
else:
    try:
        # Tenta ler a primeira aba
        df = pd.read_excel(path, nrows=10)
        print("COLUNAS:", df.columns.tolist())
        print("DADOS (primeiros 5):")
        print(df.head(5).to_string())
        
        # Verifica se alguma coluna alem do CNPJ tem dados
        stats = df.count()
        print("\\nCONTAGEM DE VALORES POR COLUNA:")
        print(stats)
        
    except Exception as e:
        print(f"ERRO ao ler Excel: {{e}}")
"""

client.exec_command("cat << 'EOF' > /tmp/check_final_excel.py\n" + check_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/check_final_excel.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
