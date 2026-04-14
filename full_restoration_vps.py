import paramiko
import os

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'
local_root = r'C:\Users\Junior T.I\.gemini\antigravity\scratch'
remote_root = '/var/www/hemn_cloud'

def sync_file(sftp, l_item, r_item):
    print(f"Uploading {l_item} to {r_item}")
    sftp.put(l_item, r_item)

def deploy_full():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        sftp = ssh.open_sftp()

        # Files to sync in root
        core_files = ['index_vps.html', 'admin_monitor_vps.html', 'HEMN_Cloud_Server_VPS.py']
        for f in core_files:
            l = os.path.join(local_root, f)
            r = remote_root + '/' + f
            if os.path.exists(l):
                sync_file(sftp, l, r)

        # Sync static directory
        local_static = os.path.join(local_root, 'static')
        remote_static = remote_root + '/static'
        try: sftp.mkdir(remote_static)
        except: pass
        
        for item in os.listdir(local_static):
            l = os.path.join(local_static, item)
            r = remote_static + '/' + item
            if os.path.isfile(l):
                sync_file(sftp, l, r)

        sftp.close()
        
        # Ensure permissions and restart
        print("Setting permissions and restarting...")
        ssh.exec_command(f"chown -R root:root {remote_root} && chmod -R 755 {remote_root} && systemctl restart hemn_cloud || pkill -f uvicorn")
        
        ssh.close()
        print("Full Restoration Complete!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy_full()
