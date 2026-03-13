import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

# Get last 100 lines of server log
stdin, stdout, stderr = client.exec_command("journalctl -u hemn_server -n 100 --no-pager 2>/dev/null || tail -100 /var/www/hemn_cloud/server.log 2>/dev/null || tail -100 /tmp/hemn.log 2>/dev/null || echo 'NO LOG FOUND'")
print("SERVER LOGS:")
print(stdout.read().decode('utf-8', errors='replace'))

# Check deployed code - look for the isdigit fix
stdin2, stdout2, stderr2 = client.exec_command("grep -n 'isdigit\\|all_cpfs\\|smart_pad\\|zfill' /var/www/hemn_cloud/cloud_engine.py | head -30")
print("\nDEPLOYED ENGINE (key lines):")
print(stdout2.read().decode('utf-8', errors='replace'))

client.close()
