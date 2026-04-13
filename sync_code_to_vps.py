import paramiko
import os
import sys

# Local files to sync
local_path = "C:/Users/Junior T.I/.gemini/antigravity/scratch/data_analysis/"
files_to_sync = [
    "HEMN_Cloud_Server_VPS.py",
    "cloud_engine.py",
    "index.html",
    "index_vps.html",
    "admin_monitor_vps.html"
]

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"
remote_dir = "/var/www/hemn_cloud/"

def sync_code():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        sftp = client.open_sftp()
        
        # Ensure remote dir exists
        try:
            sftp.mkdir(remote_dir)
        except:
            pass
            
        for f in files_to_sync:
            l_file = os.path.join(local_path, f)
            r_file = os.path.join(remote_dir, f)
            print(f"Uploading {f} -> {remote_dir}")
            sftp.put(l_file, r_file)
            
        # Sync static folder
        local_static = os.path.join(local_path, "static")
        if os.path.exists(local_static):
            print("Uploading static folder...")
            client.exec_command(f"mkdir -p {remote_dir}/static")
            for root, dirs, files in os.walk(local_static):
                for d in dirs:
                    rel_dir = os.path.relpath(os.path.join(root, d), local_static)
                    client.exec_command(f"mkdir -p {remote_dir}/static/{rel_dir}")
                for f in files:
                    rel_file = os.path.relpath(os.path.join(root, f), local_static)
                    sftp.put(os.path.join(root, f), os.path.join(remote_dir, "static", rel_file))

        # Copy data_assets folder if it exists locally
        local_assets = os.path.join(local_path, "data_assets")
        if os.path.exists(local_assets):
            print("Uploading data_assets...")
            client.exec_command(f"mkdir -p {remote_dir}/data_assets")
            for f in os.listdir(local_assets):
                sftp.put(os.path.join(local_assets, f), os.path.join(remote_dir, "data_assets", f))
        
        sftp.close()
        
        print("Restarting hemn_cloud service...")
        client.exec_command("systemctl restart hemn_cloud")
        
        client.close()
        print("Code sync and service restart completed.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sync_code()
