import paramiko
import os

def check_performance():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        commands = [
            ("JSON FILES", "find /var/www/hemn_cloud/ -type f -name '*.json' -not -path '*/venv/*'"),
            ("MD5 CHECK ALL HTML", "find /var/www/hemn_cloud/ -type f -name '*.html' -exec md5sum {} +"),
            ("CHECK FOR EXTERNAL DATA LOADING", "grep -E 'open\(|load\(|read\(' /var/www/hemn_cloud/HEMN_Cloud_Server.py | grep -v 'def '")
        ]
        
        for title, cmd in commands:
            print(f"\n--- {title} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            if out: print(out)
            if err: print(f"Error: {err}")
            
        client.close()
    except Exception as e:
        print(f"Error connecting to VPS: {e}")

if __name__ == "__main__":
    check_performance()
