import paramiko
import os

def run_remote_migration():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    local_script = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\migrate_socios.py'
    remote_script = '/tmp/migrate_socios.py'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # Upload
        sftp = ssh.open_sftp()
        print(f"Uploading {local_script}...")
        sftp.put(local_script, remote_script)
        sftp.close()
        
        # Run
        print("Running migration on VPS...")
        stdin, stdout, stderr = ssh.exec_command(f'python3 {remote_script}')
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        ssh.close()
        print("Done.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    run_remote_migration()
