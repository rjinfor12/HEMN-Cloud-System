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
    print("--- VPS TIMEZONE REPAIR ---")
    
    # 1. Update the metadata to include the 'Z' suffix
    # We use 13:20 UTC, which the browser will show as 10:20 Brasilia
    force_ts_z = "2026-03-28T13:20:00Z"
    repair_cmds = [
        f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "INSERT OR REPLACE INTO system_metadata (key, value) VALUES (\'last_carrier_vps_timestamp\', \'{force_ts_z}\');"',
        # Also fix the FTP timestamp if it was cached without Z (though my code handles it now)
        f'sqlite3 /var/www/hemn_cloud/hemn_cloud.db "UPDATE system_metadata SET value = value || \'Z\' WHERE key = \'last_carrier_ftp_timestamp\' AND value NOT LIKE \'%Z\';"',
        # List again to verify
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
    print("\nTimezone repair completed on VPS.")
except Exception as e:
    print(f"Connection failed: {e}")
