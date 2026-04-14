import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('86.48.17.194', username='root', password='^QP67kXax9AyuvF%', timeout=20)

# Get the dismissTask function starting at line 5312
stdin, stdout, stderr = client.exec_command('cd /var/www/hemn_cloud && git show c3d9259:index_vps.html | sed -n "5312,5340p"')
output = stdout.read().decode(errors='ignore')
print("=== dismissTask function (c3d9259) ===")
print(output)

client.close()
