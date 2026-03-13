import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_comprehensive_fix():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_v3.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Fix the global_cache mapping to keep internal keys needed for logic
        # and ensure the query select is correct.
        
        # We'll use a safer string replacement for the mapping block
        target_mapping = """                        global_cache[cpf_mask] = {
                            'cnpj_completo': f"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}",
                            'razao_social': hit_dict['razao_social'], 
                            'situacao': mapping.get(situacao, 'ATIVA'),
                            'SITUACAO_CODIGO': situacao,
                            'cnae': hit_dict['cnae_fiscal'], 'logradouro': hit_dict['logradouro'], 'numero': hit_dict['numero'], 'complemento': hit_dict['complemento'],
                            'bairro': hit_dict['bairro'], 'cidade': str(hit_dict['municipio_nome']).upper(), 'uf': hit_dict['uf'], 'cep': hit_dict['cep'],
                            'ddd_novo': hit_dict['ddd1'], 'telefone_novo': hit_dict['telefone1'], 'email_novo': hit_dict['correio_eletronico'],
                            'endereco_completo': f"{hit_dict['logradouro']}, {hit_dict['numero']} - {hit_dict['bairro']} - {hit_dict['municipio_nome']}/{hit_dict['uf']}"
                        }"""
        
        # Note: We need to keep 'CNPJ' and 'SITUACAO_CODIGO' for the merge logic in Phase 2
        # Phase 2 uses df_merged['CNPJ'].isna() and global_cache[cpf_mask]['SITUACAO_CODIGO']
        
        fixed_mapping = """                        global_cache[cpf_mask] = {
                            'CNPJ': f"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}",
                            'cnpj_completo': f"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}",
                            'razao_social': hit_dict['razao_social'], 
                            'situacao': mapping.get(situacao, 'ATIVA'),
                            'SITUACAO_CODIGO': situacao,
                            'cnae': hit_dict['cnae_fiscal'], 'logradouro': hit_dict['logradouro'], 'numero': hit_dict['numero'], 'complemento': hit_dict['complemento'],
                            'bairro': hit_dict['bairro'], 'cidade': str(hit_dict['municipio_nome']).upper(), 'uf': hit_dict['uf'], 'cep': hit_dict['cep'],
                            'ddd_novo': hit_dict['ddd1'], 'telefone_novo': hit_dict['telefone1'], 'email_novo': hit_dict['correio_eletronico'],
                            'endereco_completo': f"{hit_dict['logradouro']}, {hit_dict['numero']} - {hit_dict['bairro']} - {hit_dict['municipio_nome']}/{hit_dict['uf']}"
                        }"""
        
        if target_mapping in content:
            content = content.replace(target_mapping, fixed_mapping)
        else:
            print("Warning: Target mapping block not found exactly as expected. Trying partial match.")
            # Fallback for slight variations
            content = content.replace("'cnpj_completo': f\"{str(hit_dict['cnpj_basico']).zfill(8)}", "'CNPJ': f\"{str(hit_dict['cnpj_basico']).zfill(8)}{str(hit_dict['cnpj_ordem']).zfill(4)}{str(hit_dict['cnpj_dv']).zfill(2)}\",\n                            'cnpj_completo': f\"{str(hit_dict['cnpj_basico']).zfill(8)}")

        # Also fix the final drop to include CNPJ and SITUACAO_CODIGO which were used internally
        content = content.replace("df_final = df_merged.drop(columns=['titanium_cpf', 'titanium_nome', 'mask_calc', 'lookup_key'], errors='ignore')", 
                                 "df_final = df_merged.drop(columns=['titanium_cpf', 'titanium_nome', 'mask_calc', 'lookup_key', 'CNPJ', 'SITUACAO_CODIGO'], errors='ignore')")

        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        sftp.put(local_path, remote_path)
        print("Successfully applied comprehensive fix to cloud_engine.py")
        sftp.close()
        
        # Restart service
        client.exec_command('systemctl restart hemn_cloud')
        print("Service restarted.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    apply_comprehensive_fix()
