import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)

    # Check database content
    db_path = '/var/www/hemn_cloud/hemn_cloud.db'
    
    print("Schema:")
    stdin, stdout, stderr = client.exec_command(f"sqlite3 {db_path} \".schema credit_transactions\"")
    print(stdout.read().decode())

    cmd = f"sqlite3 {db_path} \"SELECT COUNT(*) FROM credit_transactions;\""
    stdin, stdout, stderr = client.exec_command(cmd)
    count = stdout.read().decode().strip()
    print(f"Total transactions: {count}")

    cmd = f"sqlite3 {db_path} \"SELECT * FROM credit_transactions ORDER BY timestamp DESC LIMIT 5;\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print("Last 5 transactions:")
    print(stdout.read().decode())

    client.close()
except Exception as e:
    print(f"Error: {e}")
