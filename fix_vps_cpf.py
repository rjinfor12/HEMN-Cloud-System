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

# Update existing records to have 11 digits (zero padded)
print("Updating existing CPFs in ClickHouse (this may take a while)...")
# In ClickHouse, we use lpad(cpf, 11, '0')
# However, updating in MergeTree usually requires ALTER TABLE ... UPDATE
query = "ALTER TABLE hemn.leads UPDATE cpf = lpad(cpf, 11, '0') WHERE length(cpf) < 11"
cmd = f"clickhouse-client --query \"{query}\""

print(f"Executing: {cmd}")
print(run(cmd))

client.close()
