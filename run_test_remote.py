import paramiko
import os

def run_test_vps():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    local_test = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\check_cnpj.py'
    remote_test = '/var/www/hemn_cloud/check_cnpj.py'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # Upload
        sftp = ssh.open_sftp()
        print(f"Uploading {local_test}...")
        sftp.put(local_test, remote_test)
        sftp.close()
        
        # Run
        print("Running check on VPS with venv...")
        stdin, stdout, stderr = ssh.exec_command('cd /var/www/hemn_cloud && ./venv/bin/python3 check_cnpj.py')
        
        print("STDOUT:")
        print(stdout.read().decode())
        print("STDERR:")
        print(stderr.read().decode())
        
        ssh.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    run_test_vps()
