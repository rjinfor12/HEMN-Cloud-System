import paramiko
import os
import time

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Check DB
db_path = '/var/www/hemn_cloud/hemn_cloud.db'
cmd_db = f"sqlite3 {db_path} 'SELECT id, module, status, progress, message FROM background_tasks WHERE id = \"db_update_march_2026\"'"
stdin, stdout, stderr = client.exec_command(cmd_db)
db_res = stdout.read().decode().strip()

# Check Log
cmd_log = "tail -n 10 /var/www/hemn_cloud/fix_ingest.out"
stdin, stdout, stderr = client.exec_command(cmd_log)
log_res = stdout.read().decode().strip()

print("DB STATUS:")
print(db_res if db_res else "Task not found in DB yet")
print("\nLOG OUTPUT:")
print(log_res if log_res else "Log file empty or not found")

client.close()
