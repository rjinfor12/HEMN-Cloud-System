import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def deep_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("--- Internal Health Check on Contabo ---")
    commands = [
        "systemctl is-active hemn_cloud",
        "systemctl is-active nginx",
        "curl -I http://127.0.0.1:8000/areadocliente/admin/monitor/stats",
        "cat /etc/nginx/sites-enabled/hemn_cloud",
        "netstat -tlpn"
    ]
    for cmd in commands:
        print(f"\n[EXEC] {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', 'ignore'))
        print(stderr.read().decode('utf-8', 'ignore'))
        
    client.close()

if __name__ == "__main__":
    deep_check()
