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

# 1. Uncomment <listen_host>::</listen_host> in /etc/clickhouse-server/config.xml
print("Updating ClickHouse listen configuration...")
# Use sed to uncomment the line. We match the specific line with comment tags.
cmd_sed = "sed -i 's/<!-- <listen_host>::<\/listen_host> -->/<listen_host>::<\/listen_host>/' /etc/clickhouse-server/config.xml"
print(run(cmd_sed))

# 2. Restart ClickHouse to apply changes
print("Restarting clickhouse-server...")
print(run("systemctl restart clickhouse-server"))

# 3. Verify listening status
print("Verifying if ClickHouse is listening on port 8123...")
print(run("netstat -tupln | grep 8123"))

client.close()
