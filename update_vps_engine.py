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

# Update cloud_engine.py to use 'hemn.leads' instead of just 'leads'
# And fix the query to be slightly more robust if needed.
print("Updating cloud_engine.py table references...")
# We use sed to replace 'FROM leads' with 'FROM hemn.leads'
run_sed = "sed -i 's/FROM leads/FROM hemn.leads/g' /var/www/hemn_cloud/cloud_engine.py"
print(run(run_sed))

# Restart the service to apply changes
print("Restarting app service...")
print(run("systemctl restart hemn_cloud"))

client.close()
