import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def get_count(db, table):
    cmd = f"clickhouse-client -q 'SELECT count() FROM {db}.{table}'"
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    return int(res) if res else 0

tbls = ['socios', 'simples']
print(f"{'Table':<15} | {'Production':<12} | {'Update':<12} | {'Diff':<10}")
print("-" * 55)
for t in tbls:
    prod = get_count('hemn', t)
    upd = get_count('hemn_update_tmp', t)
    diff = upd - prod
    print(f"{t:<15} | {prod:<12} | {upd:<12} | {diff:<10}")

client.close()
