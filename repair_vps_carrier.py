import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=port, username=user, key_filename=key_path)
    print("--- VPS REPAIR ---")
    
    # 1. Force the current timestamp to bypass the FTP/VPS mismatch
    force_ts = "2026-03-28T13:20:00" # Current UTC roughly
    repair_cmds = [
        f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "INSERT OR REPLACE INTO system_metadata (key, value) VALUES (\'last_carrier_vps_timestamp\', \'{force_ts}\');"',
        # 2. Upgrade schema for future robustness if columns are missing
        'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "ALTER TABLE background_tasks ADD COLUMN updated_at DATETIME;" || true',
        # 3. List again to verify
        'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "SELECT key, value FROM system_metadata WHERE key LIKE \'last_carrier_%\';"'
    ]
    
    for cmd in repair_cmds:
        print(f"\nRunning: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print(out)
        if err: print(f"Output/Error: {err}")
        
    client.close()
    print("\nRepair completed on VPS.")
except Exception as e:
    print(f"Connection failed: {e}")
