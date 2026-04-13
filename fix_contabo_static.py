import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def fix_static_dir():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("Creating /var/www/hemn_cloud/static directory...")
    client.exec_command("mkdir -p /var/www/hemn_cloud/static")
    
    # Upload an empty favicon to prevent errors if needed, but the dir existence is enough for Starlette
    
    print("Restarting hemn_cloud service...")
    client.exec_command("systemctl restart hemn_cloud")
    
    print("Migration Phase 1: Core should be live now.")
    client.close()

if __name__ == "__main__":
    fix_static_dir()
