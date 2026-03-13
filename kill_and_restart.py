import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

# Kill all running ClickHouse queries
print("Killing stuck ClickHouse queries...")
print(run('''
clickhouse-client --query "
SELECT 'KILLING: ' || query_id || ' - ' || left(query, 80)
FROM system.processes
WHERE query NOT LIKE '%system.processes%'"
'''))

print(run('''
clickhouse-client --query "
KILL QUERY WHERE query NOT LIKE '%system.processes%' AND elapsed > 10" SYNC
'''))

print("Done. Restarting service...")
print(run("systemctl restart hemn_cloud && echo OK"))
client.close()
