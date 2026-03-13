import sqlite3
import pandas as pd
import os

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
cpf_alvo = "09752279473"
output_res = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08\vinculos_societarios.csv"

def search_societario_export():
    try:
        conn = sqlite3.connect(db_path)
        
        cpf_miolo = cpf_alvo[3:9] 
        print(f"Buscando por miolo {cpf_miolo} na tabela de sócios...")
        
        # Busca direta e por miolo
        query = f"""
        SELECT 
            s.cnpj_basico, 
            e.razao_social, 
            s.nome_socio, 
            s.cnpj_cpf_socio, 
            s.qualificacao_socio
        FROM socios s
        LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        WHERE s.cnpj_cpf_socio = '{cpf_alvo}' 
           OR s.cnpj_cpf_socio LIKE '%{cpf_miolo}%'
        """
        
        # Usar chunksize para não estourar memória se houver muitos resultados
        chunks = pd.read_sql_query(query, conn, chunksize=5000)
        
        first = True
        total = 0
        for chunk in chunks:
            total += len(chunk)
            chunk.to_csv(output_res, index=False, mode='w' if first else 'a', header=first, sep=';', encoding='utf-8-sig')
            first = False
            
        print(f"Busca concluída. Total de {total} registros exportados para vinculos_societarios.csv")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_societario_export()
