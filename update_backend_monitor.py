import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

# Prepare the replacement script
remote_patch_script = '/tmp/patch_monitor.py'
patch_content = """
import os

file_path = '/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''    return {
        "system": sys_stats,
        "engine": engine_stats,
        "clickhouse": ch_stats,
        "timestamp": datetime.now().isoformat()
    }'''

new_code = '''    # 4. Recent Activities
    recent_tasks = []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(\"\"\"
            SELECT id, module, status, progress, message, created_at 
            FROM background_tasks 
            ORDER BY created_at DESC LIMIT 10
        \"\"\").fetchall()
        for r in rows:
            recent_tasks.append(dict(r))
        conn.close()
    except:
        pass

    return {
        "system": sys_stats,
        "engine": engine_stats,
        "clickhouse": ch_stats,
        "recent_activities": recent_tasks,
        "timestamp": datetime.now().isoformat()
    }'''

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Patch applied successfully")
else:
    print("Old code block NOT found!")
"""

# Upload and run patch script
sftp = client.open_sftp()
with sftp.file(remote_patch_script, 'w') as f:
    f.write(patch_content)
sftp.close()

stdin, stdout, stderr = client.exec_command(f'python3 {remote_patch_script}')
print(stdout.read().decode())
print(stderr.read().decode())

# Restart the service (assuming it's managed by systemd or similar, but often just a reload of the worker if it's uvicorn/gunicorn)
# For now, I'll check how it's running
stdin, stdout, stderr = client.exec_command('ps aux | grep uvicorn')
print(stdout.read().decode())

client.close()
