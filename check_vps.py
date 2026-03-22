import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('129.121.45.136', port=22022, username='root', password='ChangeMe123!')

_, out, _ = client.exec_command('grep -n "user-menu-wrapper" /var/www/hemn_cloud/static/index.html')
result = out.read().decode()
print("user-menu-wrapper:", result if result else "NOT FOUND")

_, out2, _ = client.exec_command('grep -n "Recarregar" /var/www/hemn_cloud/static/index.html')
result2 = out2.read().decode()
print("Recarregar:", result2 if result2 else "NOT FOUND in server file")

_, out3, _ = client.exec_command('stat /var/www/hemn_cloud/static/index.html')
print("File info:", out3.read().decode())

client.close()
