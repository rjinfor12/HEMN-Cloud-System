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

print('=== INSPECAO RAW DATA CLICKHOUSE-CONNECT ===')
script = """
import clickhouse_connect
client = clickhouse_connect.get_client(host='localhost', port=8123, username='default', password='')
q = "SELECT e.razao_social as NOME_DA_EMPRESA, estab.logradouro as LOGRADOURO FROM hemn.estabelecimento estab JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico LIMIT 1"
res = client.query(q)
print('Row 0:', res.result_rows[0])
print('Types:', [type(x) for x in res.result_rows[0]])
"""

# Usando heredoc
client.exec_command("cat << 'EOF' > /tmp/inspect_raw_ch.py\n" + script + "\nEOF")
print(run("/var/www/hemn_cloud/venv/bin/python3 /tmp/inspect_raw_ch.py"))

client.close()
