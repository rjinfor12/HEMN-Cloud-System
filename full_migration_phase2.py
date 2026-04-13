import paramiko
import time
import sys

# Credentials
hostgator_ip = "129.121.45.136"
hostgator_port = 22022
hostgator_user = "root"
# Path to private key on the local machine (this script runs locally)
hostgator_key_path = "C:/Users/Junior T.I/.ssh/id_rsa"  # adjust if needed

contabo_ip = "86.48.17.194"
contabo_user = "root"
contabo_pass = "^QP67kXax9AyuvF%"

def exec_ssh(client, cmd, get_output=True):
    stdin, stdout, stderr = client.exec_command(cmd)
    if get_output:
        out = stdout.read().decode('utf-8', 'ignore')
        err = stderr.read().decode('utf-8', 'ignore')
        return out, err
    return None, None

def install_sshpass(host_client):
    print("Installing sshpass on Hostgator (if not present)...")
    out, err = exec_ssh(host_client, "apt-get update && apt-get install -y sshpass", True)
    print(out)
    if err:
        print('Error installing sshpass:', err)

def rsync_from_hostgator(host_client):
    # Use sshpass to provide Contabo password for rsync
    rsync_clickhouse = (
        f"sshpass -p '{contabo_pass}' rsync -avz --progress /var/lib/clickhouse/ {contabo_user}@{contabo_ip}:/var/lib/clickhouse/"
    )
    rsync_storage = (
        f"sshpass -p '{contabo_pass}' rsync -avz --progress /var/www/hemn_cloud/storage/ {contabo_user}@{contabo_ip}:/var/www/hemn_cloud/storage/"
    )
    print("Starting ClickHouse data transfer (this may take a while)...")
    out, err = exec_ssh(host_client, rsync_clickhouse)
    print(out)
    if err:
        print('Error during ClickHouse rsync:', err)
    print("Starting storage results transfer...")
    out, err = exec_ssh(host_client, rsync_storage)
    print(out)
    if err:
        print('Error during storage rsync:', err)

def restart_contabo_services():
    contabo_client = paramiko.SSHClient()
    contabo_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    contabo_client.connect(contabo_ip, username=contabo_user, password=contabo_pass)
    print("Restarting ClickHouse and hemn_cloud services on Contabo...")
    cmds = ["systemctl restart clickhouse-server", "systemctl restart hemn_cloud"]
    for cmd in cmds:
        out, err = exec_ssh(contabo_client, cmd)
        print(f"{cmd}: {out}\n{err}")
    # Give a few seconds for services to come up
    time.sleep(5)
    # Verify status
    for svc in ["clickhouse-server", "hemn_cloud"]:
        out, err = exec_ssh(contabo_client, f"systemctl is-active {svc}")
        print(f"{svc} status: {out.strip()}")
    # Test the web endpoint
    out, err = exec_ssh(contabo_client, "curl -I http://86.48.17.194/areadocliente/admin/monitor/stats")
    print("Endpoint check:\n", out)
    contabo_client.close()

def main():
    # Connect to Hostgator using SSH key
    host_client = paramiko.SSHClient()
    host_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        host_key = paramiko.RSAKey.from_private_key_file(hostgator_key_path)
    except Exception as e:
        print('Failed to load private key:', e)
        sys.exit(1)
    host_client.connect(hostgator_ip, port=hostgator_port, username=hostgator_user, pkey=host_key)
    # Install sshpass if needed
    install_sshpass(host_client)
    # Perform rsync transfers
    rsync_from_hostgator(host_client)
    host_client.close()
    # Restart services on Contabo and verify
    restart_contabo_services()

if __name__ == "__main__":
    main()
