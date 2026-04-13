import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def fix_all_deps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("Installing ALL possible missing dependencies on Contabo...")
    # Add python-dotenv, requests, etc.
    pkgs = "python-dotenv requests beautifulsoup4 sqlalchemy mysql-connector-python passlib bcrypt"
    cmd = f"/var/www/hemn_cloud/venv/bin/pip install {pkgs}"
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode())
    
    print("Restarting hemn_cloud service...")
    client.exec_command("systemctl restart hemn_cloud")
    
    import time
    time.sleep(5)
    
    print("Checking if service is now active...")
    stdin, stdout, stderr = client.exec_command("systemctl is-active hemn_cloud")
    print(f"Status: {stdout.read().decode().strip()}")
    
    client.close()

if __name__ == "__main__":
    fix_all_deps()
