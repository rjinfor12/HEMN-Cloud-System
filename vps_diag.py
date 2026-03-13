import paramiko

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = r'C:\Users\Junior T.I\.ssh\id_rsa'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)

commands = [
    "systemctl status hemn_server",
    "journalctl -u hemn_server -n 100",
    "ls -R /var/www/hemn_cloud/*.log",
    "cat /var/www/hemn_cloud/server_error.log | tail -50",
    "netstat -tlpn | grep 8000"
]

for cmd in commands:
    print(f"\n--- RUNNING: {cmd} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'))

client.close()
