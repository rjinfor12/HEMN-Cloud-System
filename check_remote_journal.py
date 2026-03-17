import paramiko
import os

def check_remote_journal():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- Journal Scan (8501) ---")
        stdin, stdout, stderr = client.exec_command("journalctl | grep '8501' | tail -n 20")
        print(stdout.read().decode())
        
        print("--- Checking for any .py files using port 8501 ---")
        stdin, stdout, stderr = client.exec_command("grep -r '8501' /var/www")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_remote_journal()
