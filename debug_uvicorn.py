import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def debug_uvicorn():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("--- Debugging Uvicorn Startup on Contabo ---")
    # Tentar rodar manualmente para ver o erro real
    cmd = "/var/www/hemn_cloud/venv/bin/uvicorn HEMN_Cloud_Server:app --host 127.0.0.1 --port 8000"
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Pegar as últimas linhas do output
    out = stdout.read().decode('utf-8', 'ignore')
    err = stderr.read().decode('utf-8', 'ignore')
    print("STDOUT:")
    print(out)
    print("STDERR:")
    print(err)
        
    client.close()

if __name__ == "__main__":
    debug_uvicorn()
