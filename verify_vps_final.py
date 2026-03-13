import paramiko
import sys

# Ensure stdout handles UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '129.121.45.136'
port = 22022
user = 'root'

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password='ChangeMe123!')

    stdin, stdout, stderr = client.exec_command('systemctl status hemn_cloud.service')
    status_output = stdout.read().decode('utf-8', errors='replace')
    print(status_output)

    if "active (running)" in status_output:
        print("\nSUCCESS: Service is active and running!")
    else:
        print("\nWARNING: Service is NOT running as expected.")
        print(stderr.read().decode('utf-8', errors='replace'))

    client.close()
except Exception as e:
    print(f"Error: {e}")
