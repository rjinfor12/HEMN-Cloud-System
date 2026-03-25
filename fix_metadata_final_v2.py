import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run_remote(cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    o = stdout.read().decode().strip()
    e = stderr.read().decode().strip()
    if o: print(f"OUT: {o}")
    if e: print(f"ERR: {e}")
    return o

# Use heredoc for ClickHouse to avoid quoting hell
heredoc_cmd = """
clickhouse-client -q "
TRUNCATE TABLE hemn._metadata;
INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Março/2026');
"
"""

run_remote(heredoc_cmd)
run_remote("clickhouse-client -q 'SELECT * FROM hemn._metadata'")

client.close()
