import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def fix_python_env():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Install pip if missing (unlikely but safe)
        client.exec_command("apt-get update && apt-get install -y python3-pip")
        
        # Install packages using python3 -m pip
        packages = ["fastapi", "uvicorn", "clickhouse-connect", "paramiko", "pandas", "xlsxwriter", "python-multipart", "python-dotenv", "passlib[bcrypt]", "pyjwt"]
        print(f"Installing {len(packages)} packages...")
        
        stdin, stdout, stderr = client.exec_command(f"python3 -m pip install {' '.join(packages)}")
        for line in stdout:
            print(line.strip())
            
        # Verify
        stdin, stdout, stderr = client.exec_command("python3 -c 'import fastapi; print(\"FastAPI installed\")'")
        print(stdout.read().decode().strip())
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_python_env()
