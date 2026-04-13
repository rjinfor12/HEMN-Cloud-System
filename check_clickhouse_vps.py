import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def check_clickhouse():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        # Check if package exists
        stdin, stdout, stderr = client.exec_command("dpkg -l | grep clickhouse-server")
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print(f"Status: {out}")
        
        # Check if service is active
        stdin, stdout, stderr = client.exec_command("systemctl is-active clickhouse-server")
        status = stdout.read().decode('utf-8', 'ignore').strip()
        print(f"Active: {status}")
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_clickhouse()
