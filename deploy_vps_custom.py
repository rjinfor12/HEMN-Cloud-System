import paramiko
import os

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'

local_engine = r'C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\cloud_engine.py'
remote_engine = '/var/www/hemn_cloud/cloud_engine.py'

local_index = r'C:\Users\Junior T.I\.gemini\antigravity\index_vps.html'
remote_index = '/var/www/hemn_cloud/index_vps.html'

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    
    sftp = ssh.open_sftp()
    
    print("Checking if cloud_engine.py exists at /var/www/hemn_cloud/cloud_engine.py")
    try:
        sftp.stat(remote_engine)
        print("Uploading cloud_engine.py")
        sftp.put(local_engine, remote_engine)
    except Exception as e:
        print("It might be in a different folder. Checking...")
        # Check if it's in data_analysis
        remote_engine_alt = '/var/www/hemn_cloud/data_analysis/cloud_engine.py'
        try:
            sftp.stat(remote_engine_alt)
            print("Found in data_analysis. Uploading there...")
            sftp.put(local_engine, remote_engine_alt)
        except Exception as e:
            print("Not found in data_analysis either.")

    print(f"Uploading index_vps.html to {remote_index}")
    sftp.put(local_index, remote_index)
    
    local_server = r'C:\Users\Junior T.I\.gemini\antigravity\HEMN_Cloud_Server_VPS.py.restored'
    remote_server = '/var/www/hemn_cloud/HEMN_Cloud_Server_VPS.py'
    print(f"Uploading main server script to {remote_server}")
    sftp.put(local_server, remote_server)
    
    sftp.close()
    
    print("Restarting service...")
    stdin, stdout, stderr = ssh.exec_command('systemctl restart hemn_cloud.service')
    print("Restart STDOUT:", stdout.read().decode())
    print("Restart STDERR:", stderr.read().decode())

    ssh.close()
except Exception as e:
    print("Error:", e)
