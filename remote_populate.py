import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print("--- Initializing Metadata ---")
# Use a heredoc to avoid any quote shell nightmare
init_script = """
clickhouse-client -q "INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Janeiro/2026')"
"""
client.exec_command(f"echo {repr(init_script)} > /tmp/init_db.sh")
run("bash /tmp/init_db.sh")

print("\n--- Verifying ---")
db_res = run("clickhouse-client -q 'SELECT * FROM hemn._metadata'").strip()
print(f"Metadata Table:\n{db_res}")

client.close()
