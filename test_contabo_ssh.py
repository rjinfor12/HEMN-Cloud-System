import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def test_connectivity():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to Contabo VPS at {contabo_ip}...")
        client.connect(contabo_ip, port=22, username=contabo_user, password=contabo_pass)
        print("Connected successfully!")
        
        stdin, stdout, stderr = client.exec_command("lsb_release -a")
        print("OS Version:")
        print(stdout.read().decode())
        
        stdin, stdout, stderr = client.exec_command("python3 --version")
        print("Python Version:")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_connectivity()
