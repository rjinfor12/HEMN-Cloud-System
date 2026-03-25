import paramiko
import os

hostname = "129.121.45.136"
port = 22022
username = "root"
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa")

def restart_server():
    print(f"Connecting to {hostname}:{port}...")
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, pkey=key)
    
    print("Restarting 'hemn_cloud' service...")
    stdin, stdout, stderr = client.exec_command("systemctl restart hemn_cloud")
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("Success: Server restarted.")
    else:
        print(f"Error restarting server. Exit code: {exit_status}")
        print(stderr.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    restart_server()
