import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

sql = """
CREATE TABLE IF NOT EXISTS asaas_payments (
    id TEXT PRIMARY KEY,
    username TEXT,
    amount REAL,
    credits REAL,
    status TEXT,
    pix_payload TEXT,
    pix_image_base64 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
);
"""

try:
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)
    
    # We use semicolon as separator and carefully pass to sqlite3
    cmd = f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "{sql}"'
    print(f"Executing SQL migration...")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if err:
        print(f"Error: {err}")
    else:
        print("Migration successful! Table 'asaas_payments' created.")
        
    client.close()
except Exception as e:
    print(f"Connection failed: {e}")
