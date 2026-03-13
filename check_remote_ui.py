import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'ChangeMe123!'

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)

    print("\nGETTING REMOTE FILE...")
    sftp = client.open_sftp()
    sftp.get('/var/www/hemn_cloud/static/index.html', 'remote_index_debug.html')
    sftp.close()
    print("DONE. Downloaded to remote_index_debug.html")
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
