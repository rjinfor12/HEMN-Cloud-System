import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username=user, password=password)

def run_cmd(client, cmd):
    print(f"--- Executing: {cmd} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))
    print("ERR:", stderr.read().decode('utf-8', errors='ignore'))

run_cmd(client, "systemctl status hemn_cloud_dev.service")
run_cmd(client, "journalctl -u hemn_cloud_dev.service -n 50 --no-pager")
run_cmd(client, "tail -n 20 /var/log/nginx/error.log")

client.close()
