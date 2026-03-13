import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_phase2_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_phase2_trace.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if 'df_merged = pd.merge(df_in, df_cache, on=\'lookup_key\', how=\'left\')' in line:
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: df_merged columns: {{df_merged.columns.tolist()}}")\n')
                new_lines.append(f'                print(f"DEBUG: df_merged shape: {{df_merged.shape}}")\n')
                continue
            if 'df_final = df_merged.drop(columns=[' in line:
                new_lines.append(f'                print(f"DEBUG: Attempting to drop columns from df_merged...")\n')
                new_lines.append(line)
                new_lines.append(f'                print(f"DEBUG: Drop successful. df_final columns: {{df_final.columns.tolist()}}")\n')
                continue
            new_lines.append(line)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        sftp.put(local_path, remote_path)
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("Phase 2 trace injected.")
    finally:
        client.close()

if __name__ == "__main__":
    apply_phase2_trace()
