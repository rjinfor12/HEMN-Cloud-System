import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_clean_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_trace_v2.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            # Phase 0: Input info
            if 'total = len(df_in)' in line:
                new_lines.append(line)
                new_lines.append(f'            print(f"DEBUG: Input rows: {{total}}")\n')
                continue
            
            # Phase 1: Search results
            if 'basic_list = list(basic_cnpjs)' in line:
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: basic_list size: {{len(basic_list)}}")\n')
                continue
                
            # Phase 1: Mapping
            if 'global_cache[cpf_mask] = {' in line:
                new_lines.append(line)
                # Correct move to separate line
                new_lines.append(f'\n') # Placeholder to avoid indentation issues or just insert after
                continue
            
            # Phase 2: Merge results
            if "found_count = df_merged['CNPJ'].notna().sum()" in line:
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: Merged found count: {{found_count}}")\n')
                continue
                
            # Final: Save attempt
            if 'df_final.to_excel(output_file, index=False)' in line:
                new_lines.append(f'            print(f"DEBUG: Attempting to save to: {{output_file}}")\n')
                new_lines.append(line)
                new_lines.append(f'            print(f"DEBUG: Save complete. Checking existence...")\n')
                new_lines.append(f'            print(f"DEBUG: File exists on disk: {{os.path.exists(output_file)}}")\n')
                continue
            
            new_lines.append(line)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        sftp.put(local_path, remote_path)
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("Properly formatted trace-injected version applied.")
    finally:
        client.close()

if __name__ == "__main__":
    apply_clean_trace()
