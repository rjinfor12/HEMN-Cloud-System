import sqlite3
import pandas as pd

db_path = r"\\SAMUEL_TI\cnpj-sqlite-main\dados-publicos\cnpj.db"
cpf_alvo = "09752279473"

def search_societario():
    try:
        conn = sqlite3.connect(db_path)
        
        # Procurar por CPF na tabela de sócios
        # Podemos buscar pela string exata ou parcial caso esteja mascarado (ex: 522794)
        # O padrão da RFB costuma ser ***123456**
        
        # Pegar os 6 números centrais do CPF como fallback
        cpf_miolo = cpf_alvo[3:9] 
        print(f"Buscando por CPF: {cpf_alvo} (Miolo: {cpf_miolo})...")
        
        query = f"""
        SELECT 
            s.cnpj_basico, 
            e.razao_social, 
            s.nome_socio, 
            s.cnpj_cpf_socio, 
            s.qualificacao_socio,
            s.data_entrada_sociedade
        FROM socios s
        LEFT JOIN empresas e ON s.cnpj_basico = e.cnpj_basico
        WHERE s.cnpj_cpf_socio = '{cpf_alvo}' 
           OR s.cnpj_cpf_socio LIKE '%{cpf_miolo}%'
        """
        
        df_resultados = pd.read_sql_query(query, conn)
        
        if not df_resultados.empty:
            print(f"\n[!] Encontrado(s) {len(df_resultados)} vínculo(s):")
            print(df_resultados.to_string(index=False))
        else:
            print("\nNenhum vínculo encontrado com este CPF na base de sócios.")
            
        conn.close()
    except Exception as e:
        print(f"Erro na consulta: {e}")

if __name__ == "__main__":
    search_societario()
