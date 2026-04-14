import paramiko
import time

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def finish_deployment():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=20)
    
    # 1. Restart Service
    print("Restarting service...")
    client.exec_command("systemctl stop hemn_cloud && fuser -k 8000/tcp && systemctl start hemn_cloud")
    time.sleep(5)
    
    # 2. Check Status
    print("Checking status...")
    stdin, stdout, stderr = client.exec_command("systemctl is-active hemn_cloud")
    status = stdout.read().decode().strip()
    print(f"Service status: {status}")
    
    # 3. Check Logic (Port 8000)
    stdin, stdout, stderr = client.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")
    http_code = stdout.read().decode().strip()
    print(f"HTTP response code: {http_code}")
    
    client.close()

if __name__ == "__main__":
    finish_deployment()
