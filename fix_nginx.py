import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'L$a(tXhA\t9B~gC_mQyT&pU*wYkV$z'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, port, user, password)
    
    # Check if client_max_body_size is already set
    stdin, stdout, stderr = ssh.exec_command('grep "client_max_body_size" /etc/nginx/nginx.conf || true')
    output = stdout.read().decode('utf-8')
    
    if "client_max_body_size" not in output:
        # Inject client_max_body_size 100M into the http block
        cmds = [
            "sed -i '/http {/a \\    client_max_body_size 100M;' /etc/nginx/nginx.conf",
            "nginx -t && systemctl restart nginx"
        ]
        
        for cmd in cmds:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode('utf-8'))
            print("ERRORS:", stderr.read().decode('utf-8'))
            
    else:
        # Just replace whatever it is with 100M
        print("client_max_body_size found. Replacing it.")
        cmds = [
            "sed -i 's/client_max_body_size.*/client_max_body_size 100M;/' /etc/nginx/nginx.conf",
            "nginx -t && systemctl restart nginx"
        ]
        for cmd in cmds:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode('utf-8'))
            print("ERRORS:", stderr.read().decode('utf-8'))
            
finally:
    ssh.close()
