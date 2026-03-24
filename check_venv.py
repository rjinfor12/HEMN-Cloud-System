import paramiko

def check_venv():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        stdin, stdout, stderr = ssh.exec_command('ls -F /var/www/hemn_cloud/')
        print(stdout.read().decode())
        
        ssh.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    check_venv()
