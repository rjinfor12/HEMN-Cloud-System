import paramiko
import os

def read_remote_reporters():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        paths = ["/var/www/hemn_cloud/reporter.py", "/var/www/hemn_cloud/reporters.py"]
        for path in paths:
            print(f"\n--- Reading {path} ---")
            stdin, stdout, stderr = client.exec_command(f"cat {path}")
            print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_remote_reporters()
