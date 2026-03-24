import paramiko

def debug_mei_data():
    host = "129.121.45.136"
    port = 22022
    username = "root"
    password = 'ChangeMe123!'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        # 2. Contar homônimos usando substring para o padrão novo (maioria)
        query = """
            SELECT cat, count() as total_nomes
            FROM (
                SELECT 
                    multiIf(count() = 1, 'Unico na UF', count() = 2, '2 Homonimos na UF', '3 ou mais Homonimos') as cat
                FROM (
                    SELECT 
                        trim(multiIf(razao_social REGEXP '^[0-9]{2}\\\\.[0-9]{3}\\\\.[0-9]{3} ', substring(razao_social, 12), 
                                     razao_social REGEXP ' [0-9]{11}$', substring(razao_social, 1, length(razao_social)-12),
                                     razao_social)) as nome_limpo,
                        uf
                    FROM hemn.empresas e
                    JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
                    WHERE e.natureza_juridica = '2135' AND est.situacao_cadastral = '02'
                )
                GROUP BY nome_limpo, uf
            )
            GROUP BY cat
        """
        print("\nAnálise de Homônimos por UF (MEIs Ativos):")
        stdin, stdout, stderr = ssh.exec_command('clickhouse-client --query "$(cat)"')
        stdin.write(query)
        stdin.channel.shutdown_write()
        res = stdout.read().decode()
        print(res)
        
        # 3. Resumo estatístico de homônimos
        q3 = """
            SELECT 
                multiIf(total = 1, 'Único na UF', total = 2, '2 Ocorrências', total <= 5, '3-5 Ocorrências', 'Mais de 5') as categoria,
                count() as qtd_nomes
            FROM (
                SELECT 
                    trim(regexpReplace(regexpReplace(razao_social, '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3} ', ''), ' [0-9]{11}$', '')) as cleaned_name,
                    uf, 
                    count() as total 
                FROM hemn.empresas e
                JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
                WHERE e.natureza_juridica = '2135' AND est.situacao_cadastral = '02'
                GROUP BY cleaned_name, uf
            )
            GROUP BY categoria
        """
        print("\nDistribuição de Unicidade por Nome/UF (MEIs ATIVOS):")
        stdin, stdout, stderr = ssh.exec_command(f'clickhouse-client --query "{q3}"')
        summary = stdout.read().decode()
        print(summary)
        
        # 3. Verificar quantos MEIs NÃO estão em hemn.socios (Apenas amostra)
        q3 = """
            SELECT count()
            FROM hemn.empresas e
            LEFT JOIN hemn.socios s ON e.cnpj_basico = s.cnpj_basico
            WHERE e.natureza_juridica = '2135' AND s.cnpj_basico = ''
        """
        # (Wait, ClickHouse LEFT JOIN null handling varies, let's use a subquery or check if s.cnpj_basico is null)
        q3 = """
            SELECT count() FROM hemn.empresas 
            WHERE natureza_juridica = '2135' 
            AND cnpj_basico NOT IN (SELECT cnpj_basico FROM hemn.socios)
        """
        print("\nConsultando MEIs SEM registros em SOCIOS...")
        stdin, stdout, stderr = ssh.exec_command(f'clickhouse-client --query "{q3}"')
        count_no_socio = stdout.read().decode().strip()
        print(f"Total de MEIs SEM registros em SOCIOS: {count_no_socio}")

        ssh.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    debug_mei_data()
