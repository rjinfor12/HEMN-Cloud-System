import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def fetch_poll_function():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    stdin, stdout, stderr = client.exec_command("sed -n '5580,5630p' /var/www/hemn_cloud/index_vps.html")
    print(stdout.read().decode('utf-8'))
    
    client.close()

if __name__ == "__main__":
    fetch_poll_function()
