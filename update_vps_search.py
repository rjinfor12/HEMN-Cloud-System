import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

NEW_DEEP_SEARCH = """
    def deep_search(self, name, cpf):
        \"\"\"Busca rapida unitaria no ClickHouse (Socios + MEIs) com alta assertividade\"\"\"
        if not self.ch_client:
            return pd.DataFrame()
        
        basics = []
        name_upper = str(name).strip().upper() if name else None
        cpf_clean = ''.join(filter(str.isdigit, str(cpf or "")))
        cpf_mask = f"***{cpf_clean[3:9]}**" if len(cpf_clean) >= 11 else None
        
        name_frags = name_upper.split() if name_upper else []
        name_pattern = f"%{'%'.join(name_frags)}%" if name_frags else None

        # 1. Stage 1: Exact Name + CPF Mask in SOCIOS
        if name_upper and cpf_mask:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE upper(nome_socio) = %(n)s AND cnpj_cpf_socio = %(c)s LIMIT 50",
                {'n': name_upper, 'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])

        # 2. Stage 2: MEI search in EMPRESAS (often name + CPF in razao_social)
        if name_pattern:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.empresas WHERE upper(razao_social) LIKE %(n)s LIMIT 50",
                {'n': name_pattern}
            )
            basics.extend([r[0] for r in res.result_rows])
            
            if cpf_clean and len(cpf_clean) >= 11:
                res = self.ch_client.query(
                    "SELECT DISTINCT cnpj_basico FROM hemn.empresas WHERE razao_social LIKE %(c)s LIMIT 50",
                    {'c': f"%{cpf_clean}%"}
                )
                basics.extend([r[0] for r in res.result_rows])

        # 3. Stage 3: Broad search in SOCIOS by name pattern
        if name_pattern:
             res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE upper(nome_socio) LIKE %(n)s LIMIT 50",
                {'n': name_pattern}
            )
             basics.extend([r[0] for r in res.result_rows])

        # 4. Stage 4: Search by CPF mask only (fallback)
        if cpf_mask and not basics:
            res = self.ch_client.query(
                "SELECT DISTINCT cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio = %(c)s LIMIT 50",
                {'c': cpf_mask}
            )
            basics.extend([r[0] for r in res.result_rows])

        if not basics:
            return pd.DataFrame()
        
        basics = list(set(basics))[:50]
        
        final_query = f\"\"\"
            SELECT 
                e.razao_social, 
                multiIf(est.situacao_cadastral = '02', 'ATIVA', 'BAIXADA/INATIVA') AS situacao,
                concat(est.cnpj_basico, est.cnpj_ordem, est.cnpj_dv) AS cnpj_completo,
                coalesce(s.nome_socio, e.razao_social) as nome_socio, 
                coalesce(s.cnpj_cpf_socio, 'CONSULTAR RAZAO') as cnpj_cpf_socio,
                est.correio_eletronico as email_novo,
                concat(est.logradouro, ', ', est.numero, ' - ', est.bairro, ' - ', m.descricao, '/', est.uf) as endereco_completo,
                est.ddd1 as ddd_novo,
                est.telefone1 as telefone_novo,
                multiIf(length(est.telefone1) = 9 OR (length(est.telefone1) = 8 AND substring(est.telefone1, 1, 1) IN ('6','7','8','9')), 'CELULAR', 'FIXO') as tipo_telefone
            FROM hemn.estabelecimento est
            JOIN hemn.empresas e ON est.cnpj_basico = e.cnpj_basico
            LEFT JOIN hemn.socios s ON est.cnpj_basico = s.cnpj_basico
            LEFT JOIN hemn.municipio m ON est.municipio = m.codigo
            WHERE est.cnpj_basico IN (%(basics)s)
            LIMIT 100
        \"\"\"
        
        res = self.ch_client.query(final_query, {'basics': basics})
        df = pd.DataFrame(res.result_rows, columns=res.column_names)
        
        if name_upper:
            def is_match(row):
                full_text = f"{str(row['razao_social'])} {str(row['nome_socio'])}".upper()
                matches = sum(1 for frag in name_frags if frag in full_text)
                return matches >= min(2, len(name_frags))

            df = df[df.apply(is_match, axis=1)]
            
        return df.head(50)
"""

def apply_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        with sftp.open(remote_path, 'r') as f:
            content = f.read().decode()
            
        # Find the deep_search function and replace it
        import re
        # Pattern to find def deep_search up to return df.head(50)
        pattern = re.compile(r'    def deep_search\(self, name, cpf\):.*?return df\.head\(50\)', re.DOTALL)
        
        if pattern.search(content):
            new_content = pattern.sub(NEW_DEEP_SEARCH.strip(), content)
            
            with sftp.open(remote_path, 'w') as f:
                f.write(new_content)
            print("Successfully updated deep_search in cloud_engine.py")
        else:
            print("Could not find deep_search function to replace")
            
        sftp.close()
        
        # Restart service
        print("Restarting hemn_cloud service...")
        client.exec_command('systemctl restart hemn_cloud')
        print("Service restarted.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    apply_fix()
