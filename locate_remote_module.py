import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def locate_module():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        # Using -c with double quotes escaped correctly for VPS shell
        cmd = "/var/www/hemn_cloud/venv/bin/python3 -c 'import sys; sys.path.append(\"/var/www/hemn_cloud\"); import cloud_engine; print(cloud_engine.__file__)'"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(f"STDOUT: {stdout.read().decode()}")
        print(f"STDERR: {stderr.read().decode()}")
    finally:
        client.close()

if __name__ == "__main__":
    locate_module()
