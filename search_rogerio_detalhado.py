import sqlite3
import pandas as pd
import os

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
nome_alvo = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
output_res = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08\resultado_rogerio_detalhado.csv"

def search_rogerio_extra():
    try:
        conn = sqlite3.connect(db_path)
        
        print(f"Buscando Representantes Legais com o nome: {nome_alvo}...")
        
        # 1. Busca como Representante Legal
        query_rep = f"""
        SELECT 
            s.cnpj_basico, 
            e.razao_social, 
            s.nome_socio, 
            s.nome_representante,
            s.qualificacao_representante_legal
        FROM socios s
        LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        WHERE s.nome_representante = '{nome_alvo}'
           OR s.nome_representante LIKE '%{nome_alvo}%'
        """
        df_rep = pd.read_sql_query(query_rep, conn)
        
        # 2. Verificar Status das Empresas encontradas anteriormente (18528540, 38262186)
        cnpjs_basicos = "('18528540', '38262186')"
        query_status = f"""
        SELECT 
            cnpj_basico,
            cnpj_ordem,
            cnpj_dv,
            nome_fantasia,
            situacao_cadastral,
            data_situacao_cadastral,
            cidade_exterior
        FROM estabelecimento 
        WHERE cnpj_basico IN {cnpjs_basicos}
        """
        df_status = pd.read_sql_query(query_status, conn)
        
        # Mapeamento básico de situação
        # 01 - NULA, 02 - ATIVA, 03 - SUSPENSA, 04 - INAPTA, 08 - BAIXADA
        
        print(f"\nResultados como Representante: {len(df_rep)}")
        print(f"Status das empresas encontradas: {len(df_status)}")
        
        results_found = not df_rep.empty or not df_status.empty
        
        if results_found:
            with open(output_res, 'w', encoding='utf-8-sig') as f:
                f.write(f"PESQUISA DETALHADA: {nome_alvo}\n\n")
                if not df_rep.empty:
                    f.write("--- VÍNCULOS COMO REPRESENTANTE LEGAL ---\n")
                    df_rep.to_csv(f, index=False, sep=';')
                    f.write("\n")
                if not df_status.empty:
                    f.write("--- DETALHES DAS EMPRESAS (ESTABELECIMENTO) ---\n")
                    df_status.to_csv(f, index=False, sep=';')
            
            print(f"\n[!] Resultados detalhados salvos em {output_res}")
            if not df_rep.empty:
                print("\nResumo Representante:")
                print(df_rep.to_string(index=False))
            if not df_status.empty:
                print("\nResumo Status Estabelecimentos:")
                print(df_status.to_string(index=False))
        else:
            print("\nNenhum detalhe adicional encontrado.")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_rogerio_extra()
