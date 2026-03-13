import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Task ID: a9fa923b
diag_script = r"""
import pandas as pd
import os

file_path = '/var/www/hemn_cloud/storage/results/Extracao_a9fa923b.xlsx'
if not os.path.exists(file_path):
    print(f"FILE NOT FOUND: {file_path}")
    sys.exit(1)

try:
    print(f"--- INSPECTING EXCEL FILE: {file_path} ---")
    # Read the first sheet
    df = pd.read_excel(file_path, sheet_name=0, nrows=5)
    print(f"COLUMNS IN FIRST SHEET: {df.columns.tolist()}")
    print("FIRST ROW DATA:")
    print(df.iloc[0].to_dict())
    
    # Check if there are other sheets
    xl = pd.ExcelFile(file_path)
    print(f"SHEETS FOUND: {xl.sheet_names}")
    
except Exception as e:
    print(f"ERROR READING EXCEL: {e}")
"""

print('=== INSPECCIONANDO EXCEL REAL DO USUARIO (a9fa923b) ===')
client.exec_command("cat << 'EOF' > /tmp/check_user_excel.py\n" + diag_script + "\nEOF")
stdin, stdout, stderr = client.exec_command("/var/www/hemn_cloud/venv/bin/python3 /tmp/check_user_excel.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
