import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

packages = [
    "fastapi",
    "uvicorn",
    "clickhouse-connect",
    "paramiko",
    "pandas",
    "xlsxwriter",
    "python-multipart",
    "python-dotenv",
    "passlib[bcrypt]",
    "pyjwt"
]

def install_packages():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        print("Installing python packages on Contabo...")
        # Use pip3 install
        cmd = f"pip3 install {' '.join(packages)}"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Monitor output
        for line in stdout:
            print(line.strip())
        err = stderr.read().decode()
        if err:
            print(f"STDERR: {err}")
            
        client.close()
        print("Package installation finished.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_packages()
