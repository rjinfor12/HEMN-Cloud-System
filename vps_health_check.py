import paramiko
import os

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def health_check():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        commands = [
            "echo '--- CPU/RAM ---' && free -h && uptime",
            "echo '--- SYSTEMD SERVICE ---' && systemctl status hemn_cloud --no-pager",
            "echo '--- PIP LIST ---' && /var/www/hemn_cloud/venv/bin/pip list | grep -E 'pandas|clickhouse|fastapi|openpyxl'",
            "echo '--- CLICKHOUSE STATUS ---' && systemctl status clickhouse-server --no-pager",
            "echo '--- DISK USAGE ---' && df -h /var/www/hemn_cloud",
            "echo '--- RECENT LOGS ---' && journalctl -u hemn_cloud -n 50 --no-pager",
            "echo '--- SQLITE STATUS ---' && ls -lh /var/www/hemn_cloud/*.db"
        ]
        
        for cmd in commands:
            print(f"\n> {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err: print(f"STDERR: {err}")
            
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    health_check()
