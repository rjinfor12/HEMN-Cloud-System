
import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def grep_remote(remote_path, query):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        stdin, stdout, stderr = client.exec_command(f"grep -nI '{query}' {remote_path}")
        print(stdout.read().decode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    grep_remote(sys.argv[1], sys.argv[2])
