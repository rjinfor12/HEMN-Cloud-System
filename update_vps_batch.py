import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_batch_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        # Download the current file to modify it locally and ensure perfect indentation
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_update.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 1. Update the bulk query in _run_enrich to include better mapping and MEI awareness
        # We need to find the _run_enrich method and its query
        
        new_lines = []
        skip = False
        in_query = False
        
        for i, line in enumerate(lines):
            # Phase 1 query update
            if 'q = f"""' in line and i > 240 and i < 260: # Rough location of the batch query
                new_lines.append('                    q = f"""\n')
                new_lines.append('                    SELECT \n')
                new_lines.append('                        s.cnpj_cpf_socio AS cpf_mask,\n')
                new_lines.append('                        e.razao_social, \n')
                new_lines.append('                        estab.cnpj_basico, estab.cnpj_ordem, estab.cnpj_dv, \n')
                new_lines.append('                        estab.situacao_cadastral, estab.uf, mun.descricao AS municipio_nome, \n')
                new_lines.append('                        estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, \n')
                new_lines.append('                        estab.correio_eletronico, estab.tipo_logradouro, estab.logradouro, \n')
                new_lines.append('                        estab.numero, estab.complemento, estab.bairro, estab.cep, \n')
                new_lines.append('                        estab.cnae_fiscal, estab.municipio\n')
                new_lines.append('                    FROM hemn.estabelecimento estab\n')
                new_lines.append('                    JOIN hemn.empresas e ON estab.cnpj_basico = e.cnpj_basico\n')
                new_lines.append('                    LEFT JOIN hemn.municipio mun ON estab.municipio = mun.codigo\n')
                new_lines.append('                    LEFT JOIN hemn.socios s ON s.cnpj_basico = estab.cnpj_basico\n')
                new_lines.append('                    WHERE estab.cnpj_basico IN %(keys)s\n')
                new_lines.append('                    """\n')
                skip = True
                continue
            
            if skip and '"""' in line:
                skip = False
                continue
            
            # Update the global_cache mapping to use the correct keys
            if "'CNPJ':" in line and 'global_cache' in lines[i-10:i]:
                new_lines.append("                        global_cache[cpf_mask] = {\n")
                new_lines.append("                            'cnpj_completo': f\"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}\",\n")
                new_lines.append("                            'razao_social': hit_dict['razao_social'], \n")
                new_lines.append("                            'situacao': mapping.get(situacao, 'ATIVA'),\n")
                new_lines.append("                            'SITUACAO_CODIGO': situacao,\n")
                new_lines.append("                            'cnae': hit_dict['cnae_fiscal'], 'logradouro': hit_dict['logradouro'], 'numero': hit_dict['numero'], 'complemento': hit_dict['complemento'],\n")
                new_lines.append("                            'bairro': hit_dict['bairro'], 'cidade': str(hit_dict['municipio_nome']).upper(), 'uf': hit_dict['uf'], 'cep': hit_dict['cep'],\n")
                new_lines.append("                            'ddd_novo': hit_dict['ddd1'], 'telefone_novo': hit_dict['telefone1'], 'email_novo': hit_dict['correio_eletronico'],\n")
                new_lines.append("                            'endereco_completo': f\"{hit_dict['logradouro']}, {hit_dict['numero']} - {hit_dict['bairro']} - {hit_dict['municipio_nome']}/{hit_dict['uf']}\"\n")
                new_lines.append("                        }\n")
                skip = True
                continue
                
            if skip:
                if '}' in line: skip = False
                continue
            
            if not skip:
                new_lines.append(line)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        sftp.put(local_path, remote_path)
        print("Successfully updated _run_enrich in cloud_engine.py")
        sftp.close()
        
        # Restart service
        client.exec_command('systemctl restart hemn_cloud')
        print("Service restarted.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    apply_batch_fix()
