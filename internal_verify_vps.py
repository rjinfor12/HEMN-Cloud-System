import paramiko, os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, key_filename=key_path)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='replace') + stderr.read().decode('utf-8', errors='replace')

print("--- Service Status ---")
print(run("systemctl status hemn_cloud | grep Active"))

print("\n--- Backend Code Check ---")
print(run("grep -C 2 '/user/change-password' /var/www/hemn_cloud/HEMN_Cloud_Server.py"))

print("\n--- Frontend Code Check ---")
print(run("grep 'openPasswordModal' /var/www/hemn_cloud/index_vps.html"))

print("\n--- Nginx Config Check ---")
print(run("cat /etc/nginx/sites-enabled/hemn_cloud | grep proxy_pass"))

client.close()
