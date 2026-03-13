import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def read_range(start, end):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        with sftp.open('/var/www/hemn_cloud/cloud_engine.py', 'r') as f:
            content = f.read().decode('utf-8', errors='replace')
        
        lines = content.splitlines()
        for i in range(start-1, min(end, len(lines))):
            print(f"{i+1:3}: {lines[i]}")
            
        sftp.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    read_range(start, end)
