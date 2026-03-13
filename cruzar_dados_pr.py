import pandas as pd
import os

# Caminhos
desktop_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"
file_pr_p1 = os.path.join(desktop_path, "PR P1.xlsx")
file_cobertura = os.path.join(desktop_path, "COBERTURA PR.xlsx")
output_file = os.path.join(desktop_path, "PR_Cruzamento_Geral.xlsx")

def cruzar_dados():
    print("Lendo a planilha PR P1.xlsx...")
    # Lendo apenas as colunas necessárias para ganhar tempo e memória
    # Column11 = CEP, NUMERO = Número
    df_p1 = pd.read_excel(file_pr_p1)
    
    print("Lendo a planilha COBERTURA PR.xlsx...")
    df_cobertura = pd.read_excel(file_cobertura)

    print("Processando concatenação de CEP e NÚMERO em PR P1...")
    # Em PR P1, o CEP está na 'Column11' e o Número em 'NUMERO'
    # Limpeza de dados: remover .0 de números e transformar em string
    df_p1['cep_limpo'] = df_p1['Column11'].astype(str).str.replace('.0', '', regex=False).str.strip()
    df_p1['num_limpo'] = df_p1['NUMERO'].astype(str).str.replace('.0', '', regex=False).str.strip()
    
    # Criando a chave: CEP + NUMERO
    df_p1['CHAVE_JOIN'] = df_p1['cep_limpo'] + df_p1['num_limpo']

    print("Preparando a chave na planilha de COBERTURA...")
    # Na cobertura, usamos a coluna 'CHAVE'
    df_cobertura['chave_limpa'] = df_cobertura['CHAVE'].astype(str).str.replace('.0', '', regex=False).str.strip()

    print("Realizando o cruzamento (Inner Join)...")
    # Cruzamos onde a chave concatenada de P1 é igual à chave de Cobertura
    df_resultado = pd.merge(
        df_p1, 
        df_cobertura, 
        left_on='CHAVE_JOIN', 
        right_on='chave_limpa', 
        how='inner'
    )

    print(f"Cruzamento concluído. Registros encontrados: {len(df_resultado)}")

    if len(df_resultado) > 0:
        print(f"Salvando resultado em: {output_file}")
        # Removendo colunas auxiliares de processamento
        colunas_remover = ['cep_limpo', 'num_limpo', 'CHAVE_JOIN', 'chave_limpa']
        df_final = df_resultado.drop(columns=[c for c in colunas_remover if c in df_resultado.columns])
        
        df_final.to_excel(output_file, index=False)
        print("Arquivo salvo com sucesso na Área de Trabalho.")
    else:
        print("Nenhum registro correspondente foi encontrado para salvar.")

if __name__ == "__main__":
    if not os.path.exists(file_pr_p1) or not os.path.exists(file_cobertura):
        print("Erro: Arquivos não encontrados.")
    else:
        cruzar_dados()
