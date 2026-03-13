import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    stdin, stdout, stderr = client.exec_command('journalctl -u hemn_cloud.service -n 50 --no-pager')
    print("LOGS:")
    print(stdout.read().decode())
    print("ERRORS:")
    print(stderr.read().decode())
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
