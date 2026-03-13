import paramiko
import os

HOST = '129.121.45.136'
PORT = 22022
USER = 'root'
KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')

def run_diagnostics():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, port=PORT, username=USER, key_filename=KEY_PATH)
        
        output_file = "/tmp/diag_result.txt"
        
        # 1. Broad Name Search in SOCIOS
        q1 = "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE nome_socio LIKE '%ROGERIO%ELIAS%' LIMIT 50"
        # 2. Broad Name Search in EMPRESAS (MEI)
        q2 = "SELECT razao_social, cnpj_basico FROM hemn.empresas WHERE razao_social LIKE '%ROGERIO%ELIAS%' LIMIT 50"
        # 3. CPF Mask Search in SOCIOS
        q3 = "SELECT nome_socio, cnpj_cpf_socio, cnpj_basico FROM hemn.socios WHERE cnpj_cpf_socio LIKE '%522794%' LIMIT 50"

        full_cmd = f"(echo '--- SOCIOS NAME ---'; clickhouse-client --query \\\"{q1}\\\"; echo '--- EMPRESAS NAME ---'; clickhouse-client --query \\\"{q2}\\\"; echo '--- SOCIOS CPF ---'; clickhouse-client --query \\\"{q3}\\\") > {output_file}"
        
        print(f"Executing: {full_cmd}")
        stdin, stdout, stderr = client.exec_command(full_cmd)
        stdout.read() # Wait for completion
        
        # Download result
        sftp = client.open_sftp()
        sftp.get(output_file, 'diag_result_from_vps.txt')
        sftp.close()
        print("Downloaded results to diag_result_from_vps.txt")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_diagnostics()
