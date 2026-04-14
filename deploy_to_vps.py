import paramiko

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'
remote_dir = '/var/www/hemn_cloud'

def deploy():
    try:
        print(f"Connecting to {hostname}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        
        print("Pulling changes from GitHub...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && git pull origin main")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("Restarting HEMN Service...")
        # Check for systemd service first, fallback to killing uvicorn
        stdin, stdout, stderr = ssh.exec_command("systemctl restart hemn_cloud || pkill -f uvicorn && cd /var/www/hemn_cloud && ./start_vps.sh")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        ssh.close()
        print("Deployment on VPS complete!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy()
