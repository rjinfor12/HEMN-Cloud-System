import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def check_map_data():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("--- Database Stats ---")
    cmd = "sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT count(*) FROM intelligence_coverage; SELECT count(*), source_file FROM intelligence_coverage GROUP BY source_file;'"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    print("--- Sample Data (Lat/Lng) ---")
    cmd = "sqlite3 /var/www/hemn_cloud/hemn_cloud.db 'SELECT cep, lat, lng FROM intelligence_coverage LIMIT 10;'"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    client.close()

if __name__ == "__main__":
    check_map_data()
