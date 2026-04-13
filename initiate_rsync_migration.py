import paramiko
import sys

# Hostgator info
hostgator_ip = "129.121.45.136"
hostgator_port = 22022
hostgator_user = "root"
hostgator_key_path = "C:/Users/Junior T.I/.ssh/id_rsa"

# Contabo info
contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def start_migration():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        key = paramiko.RSAKey.from_private_key_file(hostgator_key_path)
        client.connect(hostgator_ip, port=hostgator_port, username=hostgator_user, pkey=key, timeout=20)
        
        # 1. Install sshpass if missing
        print("Checking/Installing sshpass on Hostgator...")
        stdin, stdout, stderr = client.exec_command("apt-get update && apt-get install -y sshpass")
        stdout.channel.recv_exit_status()
        
        # 2. Stop clickhouse on Contabo (Safety) - No, clickhouse-server handles open files usually, 
        # but rsyncing /var/lib/clickhouse while running is risky. 
        # Actually, Hostgator CH should be stopped or in read-only mode for consistency.
        # But the user says "nobody is using it today", so we'll stop it on Hostgator, sync, then start on both.
        
        print("Stopping ClickHouse on Hostgator for consistent copy...")
        client.exec_command("systemctl stop clickhouse-server")
        
        # 3. Start Rsync for ClickHouse (93GB)
        # We'll use nohup and redirect to a log so we can monitor progress
        print("Initiating ClickHouse rsync (93GB)...")
        rsync_ch = f"nohup sshpass -p '{contabo_pass}' rsync -avz -e 'ssh -o StrictHostKeyChecking=no' /var/lib/clickhouse/ {contabo_user}@{contabo_ip}:/var/lib/clickhouse/ > /tmp/rsync_ch.log 2>&1 &"
        client.exec_command(rsync_ch)
        
        # 4. Start Rsync for Storage (5.4GB)
        print("Initiating Storage rsync (5.4GB)...")
        rsync_storage = f"nohup sshpass -p '{contabo_pass}' rsync -avz -e 'ssh -o StrictHostKeyChecking=no' /var/www/hemn_cloud/storage/ {contabo_user}@{contabo_ip}:/var/www/hemn_cloud/storage/ > /tmp/rsync_storage.log 2>&1 &"
        client.exec_command(rsync_storage)
        
        print("Migration background tasks started. Monitor with /tmp/rsync_ch.log on Hostgator.")
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_migration()
