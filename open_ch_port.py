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

# 1. Open port 8123 in UFW
print("Opening port 8123...")
print(run("ufw allow 8123/tcp"))

# 2. Check ClickHouse listen configuration
print("Checking ClickHouse config...")
print(run("grep '<listen_host>::' /etc/clickhouse-server/config.xml"))

# If it's not listening on ::, we might need to uncomment it.
# Usually, it's <listen_host>::</listen_host> or <listen_host>0.0.0.0</listen_host>

client.close()
