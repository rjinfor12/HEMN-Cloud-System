import paramiko
import os

def run_remote_diag():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        # 1. Check for any process on 8501 or similar
        print("--- Checking Network Ports (85*) ---")
        stdin, stdout, stderr = client.exec_command("netstat -tulpn | grep 85")
        print(stdout.read().decode())
        
        # 2. Search for any streamlit files in /var/www
        print("--- Searching for streamlit files in /var/www ---")
        stdin, stdout, stderr = client.exec_command("find /var/www -name '*.py' | xargs grep -l 'streamlit'")
        print(stdout.read().decode())

        # 3. Check docker containers (just in case)
        print("--- Checking Docker Containers ---")
        stdin, stdout, stderr = client.exec_command("docker ps -a")
        print(stdout.read().decode())
        
        # 4. Check Nginx for any other site configs
        print("--- Checking Nginx Sites ---")
        stdin, stdout, stderr = client.exec_command("ls /etc/nginx/sites-enabled")
        print(stdout.read().decode())

        # 5. Check if search_vps_ch.py or similar exists
        print("--- Checking for reporting scripts ---")
        stdin, stdout, stderr = client.exec_command("ls -R /var/www | grep -i 'report'")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_remote_diag()
