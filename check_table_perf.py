import paramiko, os, sys

sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='root', key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

test_script = r'''
import clickhouse_connect

ch = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')

print('=== ESTRUTURA DA TABELA hemn.empresas ===')
q = "SHOW CREATE TABLE hemn.empresas"
r = ch.query(q)
print(r.result_rows[0][0])

print('\n=== CONTAGEM DE MEIs (2135) ===')
q2 = "SELECT count() FROM hemn.empresas WHERE natureza_juridica = '2135'"
r2 = ch.query(q2)
print(f"Total MEIs: {r2.result_rows[0][0]}")
'''

sftp = client.open_sftp()
with sftp.open('/tmp/check_table_perf.py', 'w') as f:
    f.write(test_script)
sftp.close()

print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/check_table_perf.py 2>&1"))
client.close()
