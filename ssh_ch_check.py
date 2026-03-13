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
        SELECT e.razao_social as NOME_DA_EMPRESA, 
               concat(estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv) as CNPJ, 
               estab.situacao_cadastral as SITUACAO_CADASTRAL,
               estab.cnae_fiscal as CNAE, 
               estab.logradouro as LOGRADOURO,
               estab.numero as NUMERO_DA_FAIXADA,
               estab.bairro as BAIRRO,
               estab.CIDADE, estab.uf as UF, estab.cep as CEP
        FROM (
            SELECT estab.*, m.descricao as CIDADE 
            FROM hemn.estabelecimento estab 
            LEFT JOIN hemn.municipio m ON estab.municipio = m.codigo 
            LIMIT 5
        ) as estab 
        JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico
        FORMAT TabSeparatedWithNames"
    """
    
    stdin, stdout, stderr = ssh.exec_command(q)
    print("STDOUT:")
    print(stdout.read().decode('utf-8'))
    print("STDERR:")
    print(stderr.read().decode('utf-8'))
    
finally:
    ssh.close()
