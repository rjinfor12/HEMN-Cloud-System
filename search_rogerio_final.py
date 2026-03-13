import sqlite3
import pandas as pd
import os

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
nome_alvo = "ROGERIO ELIAS DO NASCIMENTO JUNIOR"
output_res = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08\resultado_rogerio_final.csv"

def search_rogerio_final():
    try:
        conn = sqlite3.connect(db_path)
        
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
        """
        df_rep = pd.read_sql_query(query_rep, conn)
        
        # 2. Detalhes dos Estabelecimentos das empresas encontradas (incluindo as MEIs)
        # 18528540 e 38262186 foram as encontradas na busca por razao_social
        cnpjs_basicos = "('18528540', '38262186')"
        query_estab = f"""
        SELECT 
            cnpj_basico,
            nome_fantasia,
            situacao_cadastral,
            data_situacao_cadastral,
            logradouro,
            numero,
            bairro,
            cep,
            uf,
            municipio,
            ddd1,
            telefone1,
            correio_eletronico
        FROM estabelecimento 
        WHERE cnpj_basico IN {cnpjs_basicos}
        """
        df_estab = pd.read_sql_query(query_estab, conn)
        
        # Mapeamento de Situação
        mapping = {'01': 'NULA', '02': 'ATIVA', '03': 'SUSPENSA', '04': 'INAPTA', '08': 'BAIXADA'}
        df_estab['situacao_desc'] = df_estab['situacao_cadastral'].map(mapping)
        
        results_found = not df_rep.empty or not df_estab.empty
        
        if results_found:
            with open(output_res, 'w', encoding='utf-8-sig') as f:
                f.write(f"RELATÓRIO DE PESQUISA: {nome_alvo}\n\n")
                if not df_rep.empty:
                    f.write("--- VÍNCULOS COMO REPRESENTANTE LEGAL ---\n")
                    df_rep.to_csv(f, index=False, sep=';')
                    f.write("\n")
                if not df_estab.empty:
                    f.write("--- DETALHES DAS EMPRESAS (ENDEREÇO E STATUS) ---\n")
                    df_estab.to_csv(f, index=False, sep=';')
            
            print(f"\n[!] Resultados finais salvos em {output_res}")
            if not df_rep.empty:
                print("\nResumo Representante:")
                print(df_rep.to_string(index=False))
            if not df_estab.empty:
                print("\nResumo Empresas:")
                print(df_estab[['cnpj_basico', 'situacao_desc', 'uf', 'municipio']].to_string(index=False))
        else:
            print("\nNenhum detalhe adicional encontrado.")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_rogerio_final()
