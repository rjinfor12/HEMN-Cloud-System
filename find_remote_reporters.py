import paramiko
import os

def find_remote_reporters():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- Finding Researcher/Reporter Scripts ---")
        stdin, stdout, stderr = client.exec_command("find /var/www -iname '*report*'")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_remote_reporters()
