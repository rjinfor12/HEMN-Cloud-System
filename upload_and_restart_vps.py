import paramiko
import os

hostname = "86.48.17.194"
port = 22
username = "root"
password = "^QP67kXax9AyuvF%"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

# Local adjusted files
local_project = r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
local_server = os.path.join(local_project, "HEMN_Cloud_Server_VPS.py")
local_engine = os.path.join(local_project, "cloud_engine.py")
local_index = os.path.join(local_project, "index_vps.html")
desktop_folder = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\NV COKPIT"

# Remote paths
remote_root = "/var/www/hemn_cloud"
remote_server = os.path.join(remote_root, "HEMN_Cloud_Server.py").replace("\\", "/")
remote_engine = os.path.join(remote_root, "cloud_engine.py").replace("\\", "/")

def upload_and_restart():
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {hostname}...")
    client.connect(hostname, port=port, username=username, pkey=key if os.path.exists(ssh_key_path) else None, password=password)
    
    # Ensure remote directories exist
    client.exec_command(f"mkdir -p {remote_root}/storage/results {remote_root}/storage/uploads {remote_root}/static")
    
    sftp = client.open_sftp()
    
    print(f"Uploading server code to {remote_server}...")
    sftp.put(local_server, remote_server)
    
    print(f"Uploading engine code to {remote_engine}...")
    sftp.put(local_engine, remote_engine)
    
    print("Uploading static assets...")
    sftp.put(os.path.join(local_project, "static", "index.html"), f"{remote_root}/static/index.html")
    sftp.put(os.path.join(local_project, "static", "design-system.css"), f"{remote_root}/static/design-system.css")
    sftp.put(local_index, f"{remote_root}/index_vps.html")

    # MIGRATION: Upload spreadsheets from Desktop "NV COKPIT"
    if os.path.exists(desktop_folder):
        print(f"\n[MIGRATION] Scanning Desktop folder: {desktop_folder}")
        for f in os.listdir(desktop_folder):
            if f.lower().endswith(('.xlsx', '.csv')):
                local_path = os.path.join(desktop_folder, f)
                remote_path = f"{remote_root}/storage/results/{f}"
                
                # Check if file exists and has same size to skip
                try:
                    remote_stat = sftp.stat(remote_path)
                    local_stat = os.stat(local_path)
                    if remote_stat.st_size == local_stat.st_size:
                        print(f"  - Skipping {f} (already exists with same size)")
                        continue
                except IOError:
                    pass
                
                print(f"  - Uploading {f} ({os.path.getsize(local_path) / 1024 / 1024:.1f} MB)...")
                sftp.put(local_path, remote_path)
    
    # MIGRATION: Upload local results
    local_results = os.path.join(local_project, "storage", "results")
    if os.path.exists(local_results):
        print(f"\n[MIGRATION] Scanning project results: {local_results}")
        for f in os.listdir(local_results):
            if f.lower().endswith(('.xlsx', '.csv')):
                local_path = os.path.join(local_results, f)
                remote_path = f"{remote_root}/storage/results/{f}"
                try:
                    remote_stat = sftp.stat(remote_path)
                    if remote_stat.st_size == os.stat(local_path).st_size:
                        continue
                except IOError: pass
                
                print(f"  - Uploading {f}...")
                sftp.put(local_path, remote_path)
    
    sftp.close()
    
    sftp.close()
    
    print("\n[CLEANUP] Stopping services and killing stale processes...")
    client.exec_command("systemctl stop hemn_cloud")
    client.exec_command("systemctl stop hemn_cloud_dev")
    client.exec_command("pkill -9 python3")
    import time
    time.sleep(3)
    
    print("Restarting primary service hemn_cloud...")
    client.exec_command("systemctl restart hemn_cloud")
    
    print("Deployment and Progressive Migration complete.")
    client.close()

if __name__ == "__main__":
    upload_and_restart()
