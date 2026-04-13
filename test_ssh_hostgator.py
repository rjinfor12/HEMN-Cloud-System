import paramiko
import sys

ip = "129.121.45.136"
port = 22022
user = "root"
key_path = "C:/Users/Junior T.I/.ssh/id_rsa"

try:
    key = paramiko.RSAKey.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, pkey=key, timeout=10)
    stdin, stdout, stderr = client.exec_command("echo 'SUCCESS_HOSTGATOR'")
    print(stdout.read().decode().strip())
    client.close()
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
