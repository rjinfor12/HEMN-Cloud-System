import sqlite3
import pandas as pd
import os

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
cpf_alvo = "09752279473"
nome_alvo = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
output_res = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08\resultado_rogerio.csv"

def search_rogerio():
    try:
        conn = sqlite3.connect(db_path)
        
        print(f"Buscando vínculos para: {nome_alvo} ({cpf_alvo})...")
        
        # 1. Busca na tabela de Sócios pelo Nome Completo Exato
        query_socios = f"""
        SELECT 
            s.cnpj_basico, 
            e.razao_social, 
            s.nome_socio, 
            s.cnpj_cpf_socio, 
            s.qualificacao_socio,
            s.data_entrada_sociedade
        FROM socios s
        LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        WHERE s.nome_socio = '{nome_alvo}'
           OR s.nome_socio LIKE '%{nome_alvo}%'
        """
        df_socios = pd.read_sql_query(query_socios, conn)
        
        # 2. Busca na tabela de Empresas (Razão Social) pelo Nome ou CPF (MEI)
        query_empresas = f"""
        SELECT 
            cnpj_basico, 
            razao_social, 
            natureza_juridica
        FROM empresas 
        WHERE razao_social LIKE '%{nome_alvo}%'
           OR razao_social LIKE '%{cpf_alvo}%'
        """
        df_empresas = pd.read_sql_query(query_empresas, conn)
        
        # Combinar resultados
        print(f"\nResultados em Sócios: {len(df_socios)}")
        print(f"Resultados em Empresas (Razão Social): {len(df_empresas)}")
        
        if not df_socios.empty or not df_empresas.empty:
            # Salvar resultados
            with open(output_res, 'w', encoding='utf-8-sig') as f:
                f.write(f"PESQUISA: {nome_alvo} / {cpf_alvo}\n\n")
                if not df_socios.empty:
                    f.write("--- VÍNCULOS EM SOCIEDADES ---\n")
                    df_socios.to_csv(f, index=False, sep=';')
                    f.write("\n")
                if not df_empresas.empty:
                    f.write("--- EMPRESAS COM ESTE NOME/CPF NA RAZÃO SOCIAL ---\n")
                    df_empresas.to_csv(f, index=False, sep=';')
            
            print(f"\n[!] Sucesso! Resultados salvos em {output_res}")
            if not df_socios.empty:
                print("\nResumo Sócios:")
                print(df_socios.to_string(index=False))
            if not df_empresas.empty:
                print("\nResumo Empresas:")
                print(df_empresas.to_string(index=False))
        else:
            print("\nNenhum registro encontrado para este nome e CPF.")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_rogerio()
