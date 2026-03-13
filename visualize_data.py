import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

# Caminhos
caminho_csv = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\FEVEREIRO Q2_c+_P2.csv"
desktop_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"
output_dir = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08"
output_excel_brain = os.path.join(output_dir, 'dashboard_contatos.xlsx')
output_excel_desktop = os.path.join(desktop_path, 'Dashboard_Contatos_UF.xlsx')

def add_labels(ax):
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', 
                   (p.get_x() + p.get_width() / 2., p.get_height()), 
                   ha='center', va='center', 
                   xytext=(0, 9), 
                   textcoords='offset points',
                   fontsize=9)

def gerar_graficos_e_excel():
    print("Lendo o arquivo CSV...")
    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8')

    print("Processando dados...")
    uf_counts = df['ESTADO'].value_counts()
    
    # --- GERAÇÃO DO EXCEL ---
    print(f"Gerando arquivo Excel multi-aba...")
    with pd.ExcelWriter(output_excel_brain, engine='xlsxwriter') as writer:
        uf_summary = uf_counts.reset_index()
        uf_summary.columns = ['ESTADO', 'TOTAL_CONTATOS']
        uf_summary.to_excel(writer, sheet_name='RESUMO_GERAL', index=False)
        
        for uf in sorted(df['ESTADO'].unique().astype(str)):
            if uf and uf != 'nan':
                df_uf = df[df['ESTADO'] == uf]
                df_uf.to_excel(writer, sheet_name=uf, index=False)
                
    # Copiar para o Desktop
    try:
        shutil.copy(output_excel_brain, output_excel_desktop)
        print(f"Arquivo copiado com sucesso para: {output_excel_desktop}")
    except Exception as e:
        print(f"Erro ao copiar para o Desktop: {e}")

    # --- GRÁFICOS ---
    plt.style.use('ggplot')
    top_uf = uf_counts.head(15)
    plt.figure(figsize=(12, 7))
    ax1 = top_uf.plot(kind='bar', color='skyblue')
    add_labels(ax1)
    plt.title('Contatos por Estado (Top 15)')
    plt.xlabel('Estado')
    plt.ylabel('Quantidade')
    plt.ylim(0, top_uf.max() * 1.15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'grafico_ufs.png'))

    print("Processo concluído.")

if __name__ == "__main__":
    if not os.path.exists(caminho_csv):
        print(f"Erro: Arquivo não encontrado em {caminho_csv}")
    else:
        gerar_graficos_e_excel()
