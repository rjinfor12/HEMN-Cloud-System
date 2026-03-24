import pandas as pd

def analyze_uf():
    output_file = r"C:\Users\Junior T.I\Downloads\Enriquecido_dff3359e.xlsx"
    
    try:
        df_out = pd.read_excel(output_file).fillna('')
        
        print(f"--- Distribuição por UF no Enriquecido ({len(df_out)} linhas) ---")
        if 'UF_END' in df_out.columns:
            print(df_out['UF_END'].value_counts().head(10))
        else:
            print("Coluna 'UF_END' não encontrada.")
            
        print("\n--- Top 10 Chaves com mais resultados no Output ---")
        top_keys = df_out['CHAVE DO SOCIO'].value_counts().head(10)
        for name_key, count in top_keys.items():
            subset = df_out[df_out['CHAVE DO SOCIO'] == name_key]
            ufs = subset['UF_END'].value_counts().to_dict()
            print(f"Sócio: {name_key} | Total Empresas: {count} | Distribuição UF: {ufs}")
            
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    analyze_uf()
