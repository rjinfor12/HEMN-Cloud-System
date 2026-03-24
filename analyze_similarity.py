import pandas as pd

def analyze_similarity():
    input_file = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\testeof.xlsx"
    output_file = r"C:\Users\Junior T.I\Downloads\Enriquecido_edc05b6a.xlsx"
    
    try:
        df_in = pd.read_excel(input_file).fillna('')
        df_out = pd.read_excel(output_file).fillna('')
        
        # Identificar coluna de CPF no input
        cpf_cols = [c for c in df_in.columns if 'CPF' in c.upper() or 'DOC' in c.upper()]
        if not cpf_cols:
            print("Erro: Não encontrei coluna de CPF no input.")
            return
        cpf_col = cpf_cols[0]
        
        # Amostra do input
        sample_in = df_in.head(5).copy()
        sample_in['mask'] = sample_in[cpf_col].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11).apply(lambda x: f"***{x[3:9]}**")
        
        print("--- Amostra do Arquivo de ENTRADA (testeof) ---")
        print(sample_in[[cpf_col, 'mask']])
        
        print("\n--- Analisando Correspondência no SAÍDA (Enriquecido) ---")
        # Vamos ver se pegamos um CPF da amostra e buscamos no output (usando a máscara ou o original se existir)
        first_mask = sample_in['mask'].iloc[0]
        match_out = df_out[df_out['CHAVE DO SOCIO'].str.contains(first_mask, na=False, regex=False)]
        
        print(f"\nBusca no output pela máscara {first_mask}:")
        if not match_out.empty:
            print(f"Encontradas {len(match_out)} linhas.")
            print(match_out[['CHAVE DO SOCIO', 'CNPJ', 'RAZAO_SOCIAL']].head(5))
        else:
            print("Nenhum match encontrado para a primeira máscara do input.")
            
        print("\n--- O Problema das Máscaras Repetidas ---")
        top_masks = df_out['CHAVE DO SOCIO'].str.extract(r'(\*\*\*.*\*\*)')[0].value_counts().head(5)
        print("Top 5 máscaras que mais aparecem no Output:")
        print(top_masks)
        
        # Verificar se a máscara '***029113**' (que vi antes) está no input
        target_mask = '***029113**'
        in_has_target = sample_in['mask'].str.contains(target_mask).any() or (df_in[cpf_col].astype(str).str.contains('029113').any())
        print(f"\nA máscara {target_mask} existe no arquivo de ENTRADA? {'SIM' if in_has_target else 'NÃO'}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    analyze_similarity()
