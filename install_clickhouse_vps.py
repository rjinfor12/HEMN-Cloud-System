import paramiko
import sys

ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

commands = [
    "apt-get update",
    "apt-get install -y apt-transport-https ca-certificates dirmngr",
    "GNUPGHOME=$(mktemp -d) gpg --no-default-keyring --keyring /usr/share/keyrings/clickhouse-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 8919F6BD2B48D754",
    "echo \"deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main\" | tee /etc/apt/sources.list.d/clickhouse.list",
    "apt-get update",
    "DEBIAN_FRONTEND=noninteractive apt-get install -y clickhouse-server clickhouse-client",
    "systemctl start clickhouse-server",
    "systemctl enable clickhouse-server",
    "systemctl status clickhouse-server"
]

def run_commands():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            # We need to wait for each command to finish
            exit_status = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            print(f"STDOUT: {out}")
            if err:
                print(f"STDERR: {err}")
            if exit_status != 0:
                print(f"Command failed with status {exit_status}")
                # Don't necessarily stop if it's already installed or error message is warning
        client.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_commands()
