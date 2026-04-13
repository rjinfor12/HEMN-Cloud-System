import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
# Use the same key path as the user's script
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=port, username=user, key_filename=key_path)
    print("--- VPS DIAGNOSTIC ---")
    
    commands = [
        'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT key, value FROM system_metadata WHERE key LIKE \'last_carrier_%\';"',
        'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT id, module, status, progress, created_at, updated_at FROM background_tasks WHERE module = \'CARRIER_UPDATE\' ORDER BY created_at DESC LIMIT 3;"',
        'date -u'
    ]
    
    for cmd in commands:
        print(f"\nCommand: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(out)
        if err: print(f"Error: {err}")
        
    client.close()
except Exception as e:
    print(f"Connection failed: {e}")
