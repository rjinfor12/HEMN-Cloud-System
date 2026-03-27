import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!' # Use the real password here

def check_vps():
    print(f"Connecting to {host}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, password=password, timeout=10)
        print("Connected!")
        
        # Check index_vps.html
        print("\nChecking /var/www/hemn_cloud/index_vps.html content...")
        stdin, stdout, stderr = client.exec_command('grep -n "replace(/M" /var/www/hemn_cloud/index_vps.html')
        res = stdout.read().decode('utf-8')
        if res:
            print(f"FOUND NEW CODE:\n{res}")
        else:
            print("NEW CODE NOT FOUND! The file on the VPS is likely OLD.")
            
        # Check cloud_engine.py
        print("\nChecking /var/www/hemn_cloud/cloud_engine.py encoding...")
        stdin, stdout, stderr = client.exec_command('grep -n "M\\\\u00f3vel" /var/www/hemn_cloud/cloud_engine.py')
        res = stdout.read().decode('utf-8')
        if res:
            print(f"FOUND ESCAPED STRING:\n{res}")
        else:
            print("ESCAPED STRING NOT FOUND! The engine on the VPS is likely OLD.")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_vps()
