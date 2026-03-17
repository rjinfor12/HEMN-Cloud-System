import paramiko
import os

def list_www_dirs():
    host = '129.121.45.136'
    port = 22022
    user = 'root'
    key_path = os.path.expanduser('~/.ssh/id_rsa')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        
        print("--- Listing /var/www ---")
        stdin, stdout, stderr = client.exec_command("ls -F /var/www")
        print(stdout.read().decode())
        
        print("--- Listing /etc/nginx/sites-available ---")
        stdin, stdout, stderr = client.exec_command("ls -F /etc/nginx/sites-available")
        print(stdout.read().decode())

        print("--- Checking for any .service files ---")
        stdin, stdout, stderr = client.exec_command("ls /etc/systemd/system/*.service")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_www_dirs()
