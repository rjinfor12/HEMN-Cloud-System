import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

service_content = """[Unit]
Description=HEMN Web Suite API Service
After=network.target clickhouse-server.service

[Service]
User=root
WorkingDirectory=/var/www/hemn_cloud
ExecStart=/usr/bin/python3 HEMN_Cloud_Server_VPS.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

def setup_service():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # Write service file
        print("Creating hemn_cloud.service file...")
        stdin, stdout, stderr = client.exec_command(f"echo '{service_content}' > /etc/systemd/system/hemn_cloud.service")
        stdout.channel.recv_exit_status()
        
        # Reload and start
        print("Starting hemn_cloud service...")
        client.exec_command("systemctl daemon-reload")
        client.exec_command("systemctl enable hemn_cloud")
        client.exec_command("systemctl start hemn_cloud")
        
        # Check status
        stdin, stdout, stderr = client.exec_command("systemctl status hemn_cloud")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_service()
