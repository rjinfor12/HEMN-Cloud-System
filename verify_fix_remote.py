import paramiko
import os

host = '129.121.45.136'
port = 22022
user = 'root'
key_path = os.path.expanduser('~/.ssh/id_rsa')

cpf = '09752279473'

def run_remote_ch(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, key_filename=key_path)
        ch_cmd = f'clickhouse-client -q "{command}"'
        stdin, stdout, stderr = client.exec_command(ch_cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        client.close()
        return out, err
    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    print(f"--- DIAGNOSING CPF {cpf} on VPS ---")
    
    # 1. Step 1 of deep_search: find basics
    basics_query = f"SELECT cnpj_basico, nome_socio FROM hemn.socios WHERE cnpj_cpf_socio = '{cpf}' LIMIT 10"
    out, err = run_remote_ch(basics_query)
    print("\n[STEP 1] Basics found:")
    print(out if out else "None")
    
    if out:
        basics = [line.split('\t')[0] for line in out.split('\n')]
        basics_str = ",".join([f"'{b}'" for b in basics])
        
        # 2. Current problematic query (simulation)
        problem_query = f"""
            SELECT e.razao_social, 
                   est.cnpj AS cnpj_full,
                   s.nome_socio
            FROM hemn.empresas e
            JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
            LEFT JOIN hemn.socios s ON est.cnpj = s.cnpj
            WHERE e.cnpj_basico IN ({basics_str})
            LIMIT 10
        """
        out_p, err_p = run_remote_ch(problem_query)
        print("\n[STEP 2] Current Query Result (with est.cnpj = s.cnpj):")
        print(out_p if out_p else "None/Error")
        if err_p: print(f"Error: {err_p}")
        
        # 3. Proposed fixed query
        fixed_query = f"""
            SELECT e.razao_social, 
                   est.cnpj AS cnpj_full,
                   s.nome_socio
            FROM hemn.empresas e
            JOIN hemn.estabelecimento est ON e.cnpj_basico = est.cnpj_basico
            LEFT JOIN hemn.socios s ON e.cnpj_basico = s.cnpj_basico
            WHERE e.cnpj_basico IN ({basics_str})
              AND (s.cnpj_cpf_socio = '{cpf}' OR s.nome_socio LIKE 'ROGERIO%')
            LIMIT 10
        """
        out_f, err_f = run_remote_ch(fixed_query)
        print("\n[STEP 3] Fixed Query Result (with e.cnpj_basico = s.cnpj_basico):")
        print(out_f if out_f else "None/Error")
        if err_f: print(f"Error: {err_f}")
