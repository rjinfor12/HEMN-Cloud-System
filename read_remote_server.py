import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

print("--- DISK SPACE ---")
stdin, stdout, stderr = client.exec_command("df -h /")
print(stdout.read().decode('utf-8'))

print("--- NGINX ACCESS LOGS (Last 20) ---")
stdin, stdout, stderr = client.exec_command("tail -n 20 /var/log/nginx/access.log")
print(stdout.read().decode('utf-8'))

print("--- NGINX ERROR LOGS (Last 20) ---")
stdin, stdout, stderr = client.exec_command("tail -n 20 /var/log/nginx/error.log")
print(stdout.read().decode('utf-8'))

print("--- HEMN CLOUD LOGS (Latest) ---")
stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 50 --no-pager")
print(stdout.read().decode('utf-8'))

client.close()
