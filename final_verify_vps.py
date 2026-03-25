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

print("--- Checking 'db-version-row' in index_vps.html ---")
count = run("grep -c 'db-version-row' /var/www/hemn_cloud/index_vps.html").strip()
print(f"Occurrences: {count}")

print("\n--- Checking metadata in ClickHouse ---")
# Using a temp file to avoid quoting issues
client.exec_command("echo \"SELECT * FROM hemn._metadata\" > /tmp/query.sql")
db_res = run("clickhouse-client < /tmp/query.sql")
print(f"Metadata Table:\n{db_res}")

client.close()
