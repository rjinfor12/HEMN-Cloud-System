import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')
remote_base = '/var/www/hemn_cloud'

# Local -> Remote mappings
sync_map = {
    'index_vps.html': ['index_vps.html', 'static/index_vps.html'],
    'cloud_engine.py': ['cloud_engine.py'],
    'HEMN_Cloud_Server.py': ['HEMN_Cloud_Server.py']
}

def sync():
    print(f"Connecting to {host}:{port}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key_path)
    
    sftp = client.open_sftp()
    
    for local_file, remote_files in sync_map.items():
        local_path = os.path.join(os.getcwd(), local_file)
        if not os.path.exists(local_path):
            print(f"Warning: Local file {local_file} not found!")
            continue
            
        for remote_file in remote_files:
            remote_path = f"{remote_base}/{remote_file}"
            print(f"Uploading {local_file} -> {remote_path}...")
            sftp.put(local_path, remote_path)
            
    sftp.close()
    
    print("Restarting 'hemn_cloud' service...")
    client.exec_command("systemctl restart hemn_cloud")
    
    # Initialize DB while we are at it
    client.exec_command("clickhouse-client -q \"TRUNCATE TABLE hemn._metadata\"")
    client.exec_command("clickhouse-client -q \"INSERT INTO hemn._metadata (key, value) VALUES ('db_version', 'Janeiro/2026')\"")
    
    client.close()
    print("Sync, Insert and Restart complete.")

if __name__ == "__main__":
    sync()
