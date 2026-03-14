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

# Update cloud_engine.py to use 'SELECT DISTINCT'
print("Applying SELECT DISTINCT to cloud_engine.py...")
run_sed = "sed -i 's/SELECT cpf, nome/SELECT DISTINCT cpf, nome/g' /var/www/hemn_cloud/cloud_engine.py"
print(run(run_sed))

# Restart the service to apply changes
print("Restarting app service...")
print(run("systemctl restart hemn_cloud"))

client.close()
