import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run_ch(query):
    print(f"Executing: {query}")
    cmd = f'clickhouse-client -q "{query}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    res = stdout.read().decode().strip()
    return res

# 1. Final check
print("Current metadata:")
print(run_ch("SELECT * FROM hemn._metadata"))

# 2. Force insert
print("Forcing metadata update...")
run_ch("TRUNCATE TABLE hemn._metadata")
run_ch("INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Março/2026')")

# 3. Verify
print("New metadata:")
print(run_ch("SELECT * FROM hemn._metadata"))

client.close()
