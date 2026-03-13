import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

# Overhauling deep_search to handle MEIs (searching razao_social) and using LEFT JOIN
NEW_DEEP_SEARCH = """
    def deep_search(self, name, cpf):
        \"\"\"Busca r\u00e1pida unit\u00e1ria no ClickHouse (S\u00f3cios + MEIs)\"\"\"
        if not self.ch_client:
            return pd.DataFrame()
        
        basics = []
        name_upper = str(name).strip().upper() if name else None
        cpf_clean = ''.join(filter(str.isdigit, str(cpf or "")))
        cpf_mask = f"***{cpf_clean[3:9]}**" if len(cpf_clean) >= 11 else None

        # 1. Busca por SOCIOS
        if name_upper and cpf_mask:
            res = self.ch_client.query(
                \"SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s AND cnpj_cpf_socio = %(c)s LIMIT 50\",
                {'n': f\"{name_upper}%\", 'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])
        elif cpf_mask:
            res = self.ch_client.query(\"SELECT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = %(c)s LIMIT 50\", {'c': cpf_mask})
            basics.extend([r[0] for r in res.result_rows])
        elif name_upper:
            res = self.ch_client.query(\"SELECT cnpj_basico FROM hemn.socios WHERE nome_socio LIKE %(n)s LIMIT 50\", {'n': f\"{name_upper}%\"})
            basics.extend([r[0] for r in res.result_rows])

        # 2. Busca por EMPRESAS (Essencial para MEIs onde o nome/CPF est\u00e3o na Raz\u00e3o Social)
        if name_upper:
            res = self.ch_client.query(\"SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(n)s LIMIT 50\", {'n': f\"{name_upper}%\"})
            basics.extend([r[0] for r in res.result_rows])
        
        if cpf_clean and len(cpf_clean) >= 11:
            # MEIs costumam ter o CPF no final da Raz\u00e3o Social
            res = self.ch_client.query(\"SELECT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(c)s LIMIT 50\", {'c': f\"%{cpf_clean}%\"})
            basics.extend([r[0] for r in res.result_rows])

        if not basics:
            return pd.DataFrame()
        
        basics = list(set(basics))[:50]
        
        # Filtro final: Busca os dados completos usando LEFT JOIN para n\u00e3o perder MEIs sem s\u00f3cio registrado
        final_query = f\"\"\"
            SELECT 
                e.razao_social, 
                concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS CNPJ,
                multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                coalesce(s.nome_socio, e.razao_social) as SOCIO_VINCULO, 
                coalesce(s.cnpj_cpf_socio, 'CONSULTAR RAZAO') as CPF_SOCIO,
                est.correio_eletronico as EMAIL,
                concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', m.descricao, '/', est.uf) as ENDERECO,
                concat(est.ddd1, est.telefone1) as CONTATO_DIRETO
            FROM hemn.estabelecimento est
            JOIN hemn.empresas e ON est.cnpj_basico = e.cnpj_basico
            LEFT JOIN hemn.socios s ON est.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE est.cnpj_basico IN (%(basics)s)
            LIMIT 100
        \"\"\"
        
        res = self.ch_client.query(final_query, {'basics': basics})
        df = pd.DataFrame(res.result_rows, columns=res.column_names)
        
        # Se filtramos por nome/cpf na tela, vamos garantir que o resultado contenha o termo buscado
        if name_upper:
            df = df[df.apply(lambda x: name_upper in str(x['razao_social']).upper() or name_upper in str(x['SOCIO_VINCULO']).upper(), axis=1)]
            
        return df.head(50)
"""

def update_code():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        path = '/var/www/hemn_cloud/cloud_engine.py'
        with sftp.open(path, 'r') as f:
            lines = f.readlines()
        
        start_line = -1
        end_line = -1
        for i, line in enumerate(lines):
            if "def deep_search(self, name, cpf):" in line:
                start_line = i
            if start_line != -1 and "return pd.DataFrame(res.result_rows, columns=res.column_names)" in line:
                end_line = i
        
        # If not found with the old return, try the one from my recent (failed) update
        if end_line == -1:
            for i, line in enumerate(lines):
                if start_line != -1 and "return pd.DataFrame(res.result_rows, columns=res.column_names)" in line:
                    end_line = i
                    break

        if start_line != -1:
            # Replacing everything from def till the end of the method (heuristic-based)
            # Find the next 'def ' or end of file
            next_def = len(lines)
            for j in range(start_line + 1, len(lines)):
                if lines[j].startswith("    def "):
                    next_def = j
                    break
            
            print(f"Replacing lines {start_line+1} to {next_def}")
            new_lines = lines[:start_line] + [NEW_DEEP_SEARCH] + lines[next_def:]
            
            with sftp.open(path, 'w') as f:
                f.write("".join(new_lines))
            print("Successfully updated cloud_engine.py with MEI support")
            
            client.exec_command('systemctl restart hemn_cloud')
            print("Service restarted.")
        else:
            print("Could not find deep_search function")

        sftp.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    update_code()
