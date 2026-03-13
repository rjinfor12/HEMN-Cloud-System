import paramiko, sys

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

# 2. What Python files are in the directory?
print("FILES IN DIR:")
print(run("ls -la /var/www/hemn_cloud/*.py"))

# 3. Service unit file  
print("\nSERVICE UNIT:")
print(run("cat /etc/systemd/system/hemn_cloud.service 2>/dev/null || ls /etc/systemd/system/*.service 2>/dev/null"))

# 4. Import check
print("\nIMPORTS IN SERVER:")
print(run("grep -n 'import.*cloud_engine\\|CloudEngine\\|from cloud' /var/www/hemn_cloud/HEMN_Cloud_Server.py"))

# 5. What endpoint handles enrichment?
print("\nENRICHMENT ENDPOINT:")
print(run("grep -n 'enrich\\|batch\\|enriquec' /var/www/hemn_cloud/HEMN_Cloud_Server.py | head -20"))

# 6. Check live process
print("\nPROCESS:")
print(run("pgrep -la python | grep -i hemn"))

# 7. Recent python errors from the server
print("\nRECENT SERVER OUTPUT:")
print(run("journalctl -u hemn_cloud --since '10 minutes ago' --no-pager 2>/dev/null | tail -50"))

client.close()
