import paramiko
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = r'C:/Users/Junior T.I/.ssh/id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

# Path to the file on VPS
vps_script_path = "/var/www/hemn_cloud/HEMN_Cloud_Server.py"

print("--- PATCHING VPS SERVER CODE ---")
# Use sed to add a debug print or change the response
# Actually, I'll just use a one-liner to edit the file
patch_cmd = """python3 -c "
content = open('""" + vps_script_path + """').read()
if 'X-Debug-Index' not in content:
    content = content.replace('FileResponse(vps_path)', 'FileResponse(vps_path, headers={\\\"X-Debug-Index\\\": \\\"vps-1.0\\\"})')
    open('""" + vps_script_path + """', 'w').write(content)
" """
print(run(patch_cmd))

print("--- RESTARTING SERVICE ---")
print(run("systemctl restart hemn_cloud.service"))

client.close()
