import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_granular_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_trace_granular.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if 'total = len(df_in)' in line:
                new_lines.append(line)
                new_lines.append(f'            print(f"DEBUG: Input Rows: {{total}}")\n')
                continue
            if 'search_terms = list(set(valid_cpfs + valid_masks))' in line:
                new_lines.append(line)
                new_lines.append(f'            print(f"DEBUG: Search Terms: {{len(search_terms)}}")\n')
                continue
            if 'basic_list = list(basic_cnpjs)' in line:
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: Basic List: {{len(basic_list)}}")\n')
                continue
            if 'all_details = res_details.result_rows' in line:
                new_lines.append(line)
                new_lines.append(f'                    print(f"DEBUG: Rows from ClickHouse: {{len(all_details)}}")\n')
                continue
            if 'found_count = df_merged[\'CNPJ\'].notna().sum()' in line:
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: Found Count Merged: {{found_count}}")\n')
                continue
            if 'df_final.to_excel(output_file, index=False)' in line:
                new_lines.append(f'            print(f"DEBUG: Saving to {{output_file}}...")\n')
                new_lines.append(line)
                new_lines.append(f'            print(f"DEBUG: Save complete. Exists: {{os.path.exists(output_file)}}")\n')
                continue
            new_lines.append(line)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        sftp.put(local_path, remote_path)
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("Granular trace injected.")
    finally:
        client.close()

if __name__ == "__main__":
    apply_granular_trace()
