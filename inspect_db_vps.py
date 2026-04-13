import paramiko

hostname = '86.48.17.194'
username = 'root'
password = '^QP67kXax9AyuvF%'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

stdin, stdout, stderr = ssh.exec_command('sqlite3 /var/www/hemn_cloud/hemn_cloud.db ".schema users"')
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
