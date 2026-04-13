import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=pw, timeout=10)
    stdin, stdout, stderr = client.exec_command("echo 'SUCCESS'")
    print(stdout.read().decode().strip())
    client.close()
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
