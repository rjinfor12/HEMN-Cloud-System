import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

# Improved the whole logic for deep_search including the final query
NEW_DEEP_SEARCH = """
    def deep_search(self, name, cpf):
        \"\"\"Busca r\u00e1pida unit\u00e1ria no ClickHouse com M\u00c1XIMA assertividade\"\"\"
        if not self.ch_client:
            return pd.DataFrame()
        
        basics = []
        name_upper = str(name).strip().upper() if name else None
        cpf_clean = ''.join(filter(str.isdigit, str(cpf or "")))
        cpf_mask = f"***{cpf_clean[3:9]}**" if len(cpf_clean) >= 11 else None

        # 1. Busca por SOCIOS (Principal fonte de v\u00ednculos)
        if name_upper and cpf_mask:
            # Match exato de nome e cpf_mask (Preferencial)
            res = self.ch_client.query(
                \"SELECT cnpj_basico FROM hemn.socios WHERE nome_socio = %(n)s AND cnpj_cpf_socio = %(c)s LIMIT 50\",
                {'n': name_upper, 'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])
            
            # Se n\u00e3o achou, tenta LIKE + CPF (MUITO mais assertivo que s\u00f3 CPF)
            if not basics:
                res = self.ch_client.query(
                    \"SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s AND cnpj_cpf_socio = %(c)s LIMIT 50\",
                    {'n': f\"{name_upper}%\", 'c': cpf_mask}
                )
                basics.extend([r[0] for r in res.result_rows])
        elif cpf_mask:
            # Se s\u00f3 tem CPF, tenta achar o basico exato (Aten\u00e3o: pode retornar m\u00faltiplos nomes com o mesmo mask)
            res = self.ch_client.query(
                \"SELECT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = %(c)s LIMIT 100\",
                {'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])
        elif name_upper:
            # Se s\u00f3 tem Nome
            res = self.ch_client.query(
                \"SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s LIMIT 50\",
                {'n': f\"{name_upper}%\"}
            )
            basics.extend([r[0] for r in res.result_rows])
            
        # 2. Busca por EMPRESAS (Se for Raz\u00e3o Social / MEI)
        if name_upper:
            res = self.ch_client.query(
                \"SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(n)s LIMIT 50\",
                {'n': f\"{name_upper}%\"}
            )
            basics.extend([r[0] for r in res.result_rows])

        if not basics:
            return pd.DataFrame()
        
        basics = list(set(basics))[:50]
        
        # Filtros adicionais para a query final (Garantir que s\u00f3 mostre quem foi buscado)
        final_conds = []
        if name_upper and cpf_mask:
            final_conds.append(\"(s.nome_socio LIKE %(n_f)s AND s.cnpj_cpf_socio = %(c_f)s)\")
        elif cpf_mask:
            final_conds.append(\"s.cnpj_cpf_socio = %(c_f)s\")
        elif name_upper:
            final_conds.append(\"s.nome_socio LIKE %(n_f)s\")
        
        final_where = \" AND \".join(final_conds) if final_conds else \"1=1\"
        params = {'n_f': f\"{name_upper}%\" if name_upper else \"\", 'c_f': cpf_mask or \"\"}

        query = f\"\"\"
            SELECT e.razao_social, 
                   concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS cnpj_completo,
                   multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                   s.nome_socio, s.cnpj_cpf_socio,
                   est.correio_eletronico AS email_novo,
                   concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', m.descricao, '/', est.uf) AS endereco_completo,
                   est.telefone1 AS telefone_novo,
                   est.ddd1 AS ddd_novo,
                   'FIXO' AS tipo_telefone
            FROM hemn.empresas e
            JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
            JOIN hemn.socios s ON est.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE e.cnpj_basico IN ({','.join(['%s' for _ in basics])})
            AND {final_where}
            ORDER BY multiIf(est.situacao_cadastral = '02', 1, 2)
            LIMIT 100
        \"\"\"
        
        # Combinar basics com os outros parametros
        q_params = basics + [params.get(k) for k in ['n_f', 'c_f'] if k in params]
        # Clickhouse-connect usa parametros posicionais ou nomeados. Vamos usar posicionais para a lista IN.
        # Ajustando a query para usar parametros da forma que o ch_client espera.
        
        # Na verdade, o ch_client.query aceita dicion\u00e1rio. Mas o IN \u00e9 chato.
        # Vamos reconstruir a query com seguran\u00e3a.
        
        final_query = f\"\"\"
            SELECT e.razao_social, 
                   concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS CNPJ,
                   multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                   s.nome_socio as SOCIO_VINCULO, s.cnpj_cpf_socio as CPF_SOCIO,
                   est.correio_eletronico as EMAIL,
                   concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', m.descricao, '/', est.uf) as ENDERECO,
                   concat(est.ddd1, est.telefone1) as CONTATO_DIRETO
            FROM hemn.estabelecimento est
            JOIN hemn.empresas e ON est.cnpj_basico = e.cnpj_basico
            JOIN hemn.socios s ON est.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE est.cnpj_basico IN (%(basics)s)
            AND {final_where}
            LIMIT 100
        \"\"\"
        
        res = self.ch_client.query(final_query, {
            'basics': basics,
            'n_f': f\"{name_upper}%\" if name_upper else \"\",
            'c_f': cpf_mask or \"\"
        })
        return pd.DataFrame(res.result_rows, columns=res.column_names)
"""

def update_code():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # Read the file
        path = '/var/www/hemn_cloud/cloud_engine.py'
        with sftp.open(path, 'r') as f:
            lines = f.readlines()
        
        # Find the start and end of deep_search
        start_line = -1
        end_line = -1
        for i, line in enumerate(lines):
            if "def deep_search(self, name, cpf):" in line:
                start_line = i
            # Look for the return line of deep_search
            if start_line != -1 and "return pd.DataFrame(res.result_rows, columns=res.column_names)" in line:
                end_line = i
                break
        
        if start_line != -1 and end_line != -1:
            print(f"Replacing lines {start_line+1} to {end_line+1}")
            new_lines = lines[:start_line] + [NEW_DEEP_SEARCH] + lines[end_line+1:]
            
            # Write back
            with sftp.open(path, 'w') as f:
                f.write("".join(new_lines))
            print("Successfully updated cloud_engine.py")
            
            # Restart service
            print("Restarting service...")
            client.exec_command('systemctl restart hemn_cloud')
            print("Done.")
        else:
            print(f"Could not find boundaries: start={start_line}, end={end_line}")

        sftp.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    update_code()
