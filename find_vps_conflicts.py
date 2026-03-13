import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def find_files():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        print("Searching for cloud_engine.py files...")
        cmd = "find /var/www -name cloud_engine.py"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # Check current working directory of the process
        print("\nChecking active python processes:")
        cmd = "ps aux | grep python"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    find_files()
