import paramiko
import os

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def debug_import():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    
    print("--- Detailed Import Debug on Contabo ---")
    # Tentar importar via Python puro para ver o traceback real
    cmd = "cd /var/www/hemn_cloud && ./venv/bin/python3 -c 'import HEMN_Cloud_Server; print(\"Import Success\")'"
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', 'ignore')
    err = stderr.read().decode('utf-8', 'ignore')
    print("STDOUT:")
    print(out)
    print("STDERR:")
    print(err)
        
    client.close()

if __name__ == "__main__":
    debug_import()
