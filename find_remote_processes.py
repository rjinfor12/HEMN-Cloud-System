import paramiko
import os

def find_remote_processes():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- All Running Processes (grep report/dash/streamlit) ---")
        stdin, stdout, stderr = client.exec_command("ps aux | grep -Ei 'report|dash|streamlit'")
        print(stdout.read().decode())
        
        print("--- All Listening Ports ---")
        stdin, stdout, stderr = client.exec_command("netstat -tulpn")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_remote_processes()
