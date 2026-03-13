import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Task ID: 69b04aca
# File: Extracao_69b04aca.xlsx
diag_script = r"""
import pandas as pd
import os

file_path = '/var/www/hemn_cloud/storage/results/Extracao_69b04aca.xlsx'
if not os.path.exists(file_path):
    print(f"FILE NOT FOUND: {file_path}")
    sys.exit(1)

try:
    print(f"--- INSPECTING EXCEL FILE: {file_path} ---")
    df = pd.read_excel(file_path, nrows=5)
    print(f"COLUMNS IN EXCEL: {df.columns.tolist()}")
    print("FIRST ROW IN EXCEL:")
    print(df.iloc[0].to_dict())
except Exception as e:
    print(f"ERROR READING EXCEL: {e}")
"""

print('=== INSPECCIONANDO EXCEL GERADO NA VPS ===')
client.exec_command("cat << 'EOF' > /tmp/check_excel.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/check_excel.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
