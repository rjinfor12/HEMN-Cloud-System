import paramiko
import os

def check_specs():
    host = '86.48.17.194'
    port = 22
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- VPS HARDWARE SPECS (Actual IP) ---")
        stdin, stdout, stderr = client.exec_command('free -m')
        print("RAM (MB):")
        print(stdout.read().decode())
        
        stdin, stdout, stderr = client.exec_command('nproc')
        print("CPU CORES:", stdout.read().decode().strip())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_specs()
