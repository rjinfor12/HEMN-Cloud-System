import paramiko
import sys
import requests

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def verify_vps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        print("--- Service Status ---")
        stdin, stdout, stderr = client.exec_command("systemctl is-active hemn_cloud")
        print(f"hemn_cloud: {stdout.read().decode().strip()}")
        
        stdin, stdout, stderr = client.exec_command("systemctl is-active clickhouse-server")
        print(f"clickhouse-server: {stdout.read().decode().strip()}")
        
        print("\n--- Recent Logs ---")
        stdin, stdout, stderr = client.exec_command("journalctl -u hemn_cloud -n 20 --no-pager")
        print(stdout.read().decode())
        
        client.close()
        
        print("\n--- Web Endpoint Check ---")
        try:
            r = requests.get(f"http://{ip}/areadocliente/version", timeout=5)
            print(f"Status Code: {r.status_code}")
            print(f"Response: {r.text}")
        except Exception as e:
            print(f"Web check failed: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_vps()
