import paramiko

host = '129.121.45.136'
port = 22022
user = 'root'
password = 'L$a(tXhA\t9B~gC_mQyT&pU*wYkV$z'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, port, user, password)
    
    q = """
    clickhouse-client --query="
        SELECT count(*) as total, 
               sum(CASE WHEN telefone1 != '' OR telefone2 != '' THEN 1 ELSE 0 END) as com_telefone,
               sum(CASE WHEN telefone1 != '' AND substring(telefone1,1,1) IN ('6','7','8','9') THEN 1 ELSE 0 END) as com_celular1
        FROM hemn.estabelecimento 
        WHERE situacao_cadastral = '02' AND uf = 'CE'
        FORMAT TabSeparatedWithNames"
    """
    
    stdin, stdout, stderr = ssh.exec_command(q)
    print("STDOUT:")
    print(stdout.read().decode('utf-8'))
    print("STDERR:")
    print(stderr.read().decode('utf-8'))
    
finally:
    ssh.close()
