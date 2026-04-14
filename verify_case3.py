import paramiko

hostname = "86.48.17.194"
username = "root"
password = "^QP67kXax9AyuvF%"

def verify_case3():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    
    tests = [
        # 1. Backend direto (porta 8000)
        ("Backend direto", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/"),
        # 2. Nginx local (porta 80 -> backend)
        ("Nginx HTTP", "curl -s -o /dev/null -w '%{http_code}' http://localhost/areadocliente/"),
        # 3. Nginx HTTPS via domínio (de dentro do servidor)
        ("Nginx HTTPS", "curl -s -o /dev/null -w '%{http_code}' -k https://localhost/areadocliente/"),
        # 4. Status dos serviços
        ("Serviço hemn_cloud", "systemctl is-active hemn_cloud"),
        ("Serviço nginx", "systemctl is-active nginx"),
        ("Serviço clickhouse", "systemctl is-active clickhouse-server"),
        # 5. Porta 8000 aberta
        ("Porta 8000", "ss -tlnp | grep 8000"),
        # 6. Porta 80 e 443 abertas
        ("Porta 80/443", "ss -tlnp | grep -E ':80|:443'"),
    ]
    
    for title, cmd in tests:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        err = stderr.read().decode('utf-8', 'ignore').strip()
        result = out or err or "(vazio)"
        print(f"  [{title}] -> {result}")
    
    client.close()

if __name__ == "__main__":
    verify_case3()
