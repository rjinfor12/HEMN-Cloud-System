import paramiko
import os

key_path = os.path.expanduser('~/.ssh/id_rsa')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('129.121.45.136', port=22022, username='root', key_filename=key_path)
    
    cmd = """
import pandas as pd
import os
import re
files = [f for f in os.listdir("/var/www/hemn_cloud/storage/uploads") if "CEARA" in f]
if not files:
    print("No CEARA files found")
    exit()
latest = max(["/var/www/hemn_cloud/storage/uploads/"+f for f in files], key=os.path.getctime)
print("File:", latest)
df = pd.read_csv(latest, sep=None, engine="python", dtype=str, on_bad_lines="skip")
if "CEP" not in df.columns:
    print("CEP not in columns:", df.columns.tolist())
    val = df.iloc[0, 0]
else:
    val = str(df["CEP"].iloc[0])

print("Value:", val)
print("Bytes:", val.encode("utf-8").hex())
print("After replace D:", re.sub(r"\\D", "", val))
"""
    
    stdin, stdout, stderr = ssh.exec_command(f'cd /var/www/hemn_cloud && ./venv/bin/python -c \'{cmd}\'')
    print('STDOUT:\n', stdout.read().decode())
    print('STDERR:\n', stderr.read().decode())
    
except Exception as e:
    print('Error:', e)
finally:
    ssh.close()
