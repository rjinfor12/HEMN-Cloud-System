import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def apply_path_trace():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        sftp = client.open_sftp()
        
        remote_path = '/var/www/hemn_cloud/cloud_engine.py'
        local_path = 'cloud_engine_path_trace.py'
        sftp.get(remote_path, local_path)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if 'self._update_task(tid, progress=95, message="Salvando arquivo resultante...")' in line:
                new_lines.append(line)
                new_lines.append(f'            print(f"ABS_OUTPUT_DIR: {{os.path.abspath(output_dir)}}")\n')
                new_lines.append(f'            print(f"ABS_OUTPUT_FILE: {{os.path.abspath(output_file)}}")\n')
                continue
            if 'df_final.to_excel(output_file, index=False)' in line:
                new_lines.append(f'            print(f"BEFORE_SAVE_UPLOADS: {{os.listdir(output_dir)}}")\n')
                new_lines.append(line)
                new_lines.append(f'            print(f"AFTER_SAVE_UPLOADS: {{os.listdir(output_dir)}}")\n')
                new_lines.append(f'            print(f"VERIFY_EXISTS: {{os.path.exists(output_file)}}")\n')
                continue
            new_lines.append(line)

        with open(local_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        sftp.put(local_path, remote_path)
        sftp.close()
        client.exec_command('systemctl restart hemn_cloud')
        print("Path trace version applied.")
    finally:
        client.close()

if __name__ == "__main__":
    apply_path_trace()
