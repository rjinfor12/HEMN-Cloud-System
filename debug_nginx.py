import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def debug_nginx():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("--- Contabo Nginx Debug ---")
    commands = [
        "nginx -t",
        "ls -l /etc/nginx/sites-enabled/",
        "tail -n 50 /var/log/nginx/error.log",
        "systemctl status nginx --no-pager"
    ]
    for cmd in commands:
        print(f"\n[EXEC] {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
    client.close()

if __name__ == "__main__":
    debug_nginx()
