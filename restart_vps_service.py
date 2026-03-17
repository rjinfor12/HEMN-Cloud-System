import paramiko
import os

def restart_remote_service():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- Restarting hemn_cloud.service ---")
        stdin, stdout, stderr = client.exec_command("systemctl restart hemn_cloud.service")
        stdout.channel.recv_exit_status()
        
        print("--- Checking Status ---")
        stdin, stdout, stderr = client.exec_command("systemctl status hemn_cloud.service")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    restart_remote_service()
