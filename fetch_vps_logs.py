import paramiko

def fetch_logs():
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%')
        
        # Simplest way to get the last 100 lines
        stdin, stdout, stderr = c.exec_command('tail -n 100 /var/www/hemn_cloud/cloud_engine_debug.log')
        content = stdout.read().decode('utf-8', errors='ignore')
        
        print("--- START OF VPS LOGS ---")
        print(content)
        print("--- END OF VPS LOGS ---")
        
        c.close()
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    fetch_logs()
