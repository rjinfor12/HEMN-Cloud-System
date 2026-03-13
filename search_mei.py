import sqlite3
import pandas as pd

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
cpf_alvo = "09752279473"

def search_mei_and_socios():
    try:
        conn = sqlite3.connect(db_path)
        
        print(f"Buscando CPF {cpf_alvo} na Razão Social (MEI)...")
        query_mei = f"SELECT cnpj_basico, razao_social FROM empresas WHERE razao_social LIKE '%{cpf_alvo}%'"
        df_mei = pd.read_sql_query(query_mei, conn)
        
        if not df_mei.empty:
            print(f"\n[!] MEI encontrado:")
            print(df_mei.to_string(index=False))
        else:
            print("\nNenhum MEI encontrado com este CPF na Razão Social.")

        # Buscar por nome se o usuário for o Samuel (baseado no path)
        print(f"\nBuscando vínculos de 'SAMUEL' com o miolo do CPF...")
        cpf_miolo = cpf_alvo[3:9]
        query_samuel = f"""
        SELECT 
            s.cnpj_basico, 
            e.razao_social, 
            s.nome_socio, 
            s.cnpj_cpf_socio
        FROM socios s
        LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        WHERE (s.cnpj_cpf_socio LIKE '%{cpf_miolo}%')
          AND (s.nome_socio LIKE '%SAMUEL%')
        """
        df_samuel = pd.read_sql_query(query_samuel, conn)
        
        if not df_samuel.empty:
            print(f"\n[!] Possíveis vínculos (SAMUEL + Miolo CPF):")
            print(df_samuel.to_string(index=False))
        else:
            print("\nNenhum vínculo direto 'SAMUEL' + Miolo encontrado.")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_mei_and_socios()
