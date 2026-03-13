import os
import pandas as pd
import glob
import time

target_dir = r"C:\Users\Junior T.I\Downloads\BASE NOVA_26\OI_NOVO"
output_excel = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\Consolidado_OI_NOVO.xlsx"
output_csv = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\Consolidado_OI_NOVO.csv"

def consolidar():
    start_time = time.time()
    all_files = glob.glob(os.path.join(target_dir, "*.xlsx"))
    
    print(f"Iniciando consolidação de {len(all_files)} arquivos...")
    
    consolidated_list = []
    total_linhas = 0
    
    for i, file_path in enumerate(all_files):
        nome_arquivo = os.path.basename(file_path)
        print(f"[{i+1}/{len(all_files)}] Lendo {nome_arquivo}...")
        
        try:
            # Lendo apenas as colunas necessárias para economizar memória e tempo
            df = pd.read_excel(file_path, usecols=['CLIENTE_NOME', 'DOC'])
            consolidated_list.append(df)
            total_linhas += len(df)
        except Exception as e:
            print(f"  Erro ao ler {nome_arquivo}: {e}")
            
    print(f"\nConsolidação concluída da leitura. Total de linhas lidas: {total_linhas}")
    
    if len(consolidated_list) > 0:
        print("Concatenando dataframes...")
        df_final = pd.concat(consolidated_list, ignore_index=True)
        
        # Limpar nulos se existirem nas duas colunas ao mesmo tempo
        df_final = df_final.dropna(subset=['CLIENTE_NOME', 'DOC'], how='all')
        
        linhas_finais = len(df_final)
        print(f"Total de linhas após limpeza: {linhas_finais}")
        
        limite_excel = 1000000  # Fechado em 1 milhão para dar margem de segurança ao cabeçalho (limite é 1.048.576)
        
        if linhas_finais > limite_excel:
            print(f"O número de registros excede {limite_excel}. Dividindo em múltiplas abas no arquivo Excel...")
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                num_abas = (linhas_finais // limite_excel) + 1
                for i in range(num_abas):
                    start_row = i * limite_excel
                    end_row = min((i + 1) * limite_excel, linhas_finais)
                    
                    df_aba = df_final.iloc[start_row:end_row]
                    nome_aba = f"Parte_{i+1}"
                    
                    print(f"  -> Salvando {len(df_aba)} linhas na aba '{nome_aba}'...")
                    df_aba.to_excel(writer, sheet_name=nome_aba, index=False)
                    
            print(f"Salvo em: {output_excel}")
        else:
            print("Salvando em uma única aba no Excel...")
            df_final.to_excel(output_excel, index=False)
            print(f"Salvo em: {output_excel}")
            
    print(f"Tempo total: {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    consolidar()
