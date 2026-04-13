import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def list_files():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    stdin, stdout, stderr = client.exec_command("ls -R /var/www/hemn_cloud")
    print(stdout.read().decode())
    client.close()

if __name__ == "__main__":
    list_files()
