import paramiko
import os
import sys

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    print(f"\n--- RUNNING: {cmd} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    try:
        if out: sys.stdout.buffer.write(f"STDOUT:\n{out}".encode('utf-8'))
        if err: sys.stdout.buffer.write(f"STDERR:\n{err}".encode('utf-8'))
        sys.stdout.buffer.write(b"\n")
    except:
        if out: print("Stdout received (unprintable)")
    return out, err

print("=== VPS DEEP DIAGNOSTIC ===")

# 1. Check Service Status
run("systemctl status hemn_cloud --no-pager")

# 2. Check recent logs
run("journalctl -u hemn_cloud --since '2 minutes ago' --no-pager")

# 3. Test API locally on VPS
# I'll try to find the login token first or just use a skip-auth if possible (not likely)
# Actually, I'll just check if the file on the VPS has my changes.
run("grep -C 5 'recent_activities' /var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py")
run("grep -C 5 'get_internal_stats' /var/www/hemn_cloud/cloud_engine.py")

# 4. Check Database contents
# We need to know if there ARE tasks to show.
run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT COUNT(*) FROM background_tasks;'")
run("sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT module, status, created_at FROM background_tasks ORDER BY created_at DESC LIMIT 5;'")

# 5. Check Ingestion Log existence on VPS
run("ls -lh /var/www/hemn_cloud/ingest_march_2026.log")

client.close()
