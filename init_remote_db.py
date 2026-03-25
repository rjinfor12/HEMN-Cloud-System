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

print("--- Initializing Metadata in ClickHouse ---")
# Drop and Recreate to be sure
run("clickhouse-client --query='CREATE TABLE IF NOT EXISTS hemn._metadata (key String, value String) ENGINE = TinyLog'")
run("clickhouse-client --query=\"INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Janeiro/2026')\"")

print("\n--- Verifying ---")
db_res = run("clickhouse-client --query='SELECT * FROM hemn._metadata'").strip()
print(f"Metadata Table:\n{db_res}")

client.close()
