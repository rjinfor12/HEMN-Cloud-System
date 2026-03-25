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

# Create and insert in one go to avoid multi-command complexity
sql = """
CREATE TABLE IF NOT EXISTS hemn._metadata (key String, value String) ENGINE = MergeTree() ORDER BY key;
INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Janeiro/2026');
"""
# Use heredoc for multi-line SQL
remote_cmd = f"clickhouse-client --multiline --query \"{sql}\""
print(run(remote_cmd))

print('=== FINAL CONTENT ===')
print(run("clickhouse-client --query 'SELECT * FROM hemn._metadata'"))

client.close()
