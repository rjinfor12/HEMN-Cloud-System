import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def debug_vps():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("Checking ClickHouse connection and metadata...")
    # This command creates a temporary python script on the VPS to test the engine
    cmd = """
cd /var/www/hemn_cloud
python3 -c "
from cloud_engine import CloudEngine
engine = CloudEngine()
print('DB Version:', engine.get_db_version())
print('Carrier Status:', engine.get_carrier_status() if hasattr(engine, 'get_carrier_status') else 'No method')
"
"""
    stdin, stdout, stderr = client.exec_command(cmd)
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())
    
    print("\nChecking system logs for 404s...")
    stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 50 --no-pager")
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    debug_vps()
