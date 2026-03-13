import paramiko
import os
import subprocess

host = '129.121.45.136'
port = 22022
user = 'root'
password = '1304@Ev19'

ssh_dir = os.path.expanduser('~/.ssh')
key_path = os.path.join(ssh_dir, 'id_rsa')
pub_key_path = key_path + '.pub'

if not os.path.exists(ssh_dir):
    os.makedirs(ssh_dir)

if not os.path.exists(key_path):
    print("Generating new SSH key...")
    subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', key_path, '-q', '-N', ''])

with open(pub_key_path, 'r') as f:
    pub_key = f.read().strip()

print(f"Connecting to {host}:{port} as {user}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(host, port=port, username=user, password=password)
    print("Connected! Uploading public key...")
    
    # Create .ssh directory on the server if it doesn't exist
    client.exec_command('mkdir -p ~/.ssh')
    client.exec_command('chmod 700 ~/.ssh')
    
    # Append the public key to authorized_keys
    command = f'echo "{pub_key}" >> ~/.ssh/authorized_keys'
    client.exec_command(command)
    client.exec_command('chmod 600 ~/.ssh/authorized_keys')
    
    print("Key uploaded successfully! You can now SSH without password.")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
