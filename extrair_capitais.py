import pandas as pd
import os
import shutil

# Caminhos
caminho_csv = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\FEVEREIRO Q2_c+_P2.csv"
desktop_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho"
output_dir = r"C:\Users\Junior T.I\.gemini\antigravity\brain\64e42803-1a02-4d33-a471-01ac5c73bb08"
output_capitais_brain = os.path.join(output_dir, 'capitais_contatos.xlsx')
output_capitais_desktop = os.path.join(desktop_path, 'Capitais_Contatos.xlsx')

# Mapeamento de Capitais
capitais_map = {
    'AC': 'RIO BRANCO',
    'AL': 'MACEIO',
    'AP': 'MACAPA',
    'AM': 'MANAUS',
    'BA': 'SALVADOR',
    'CE': 'FORTALEZA',
    'DF': 'BRASILIA',
    'ES': 'VITORIA',
    'GO': 'GOIANIA',
    'MA': 'SAO LUIS',
    'MT': 'CUIABA',
    'MS': 'CAMPO GRANDE',
    'MG': 'BELO HORIZONTE',
    'PA': 'BELEM',
    'PB': 'JOAO PESSOA',
    'PR': 'CURITIBA',
    'PE': 'RECIFE',
    'PI': 'TERESINA',
    'RJ': 'RIO DE JANEIRO',
    'RN': 'NATAL',
    'RS': 'PORTO ALEGRE',
    'RO': 'PORTO VELHO',
    'RR': 'BOA VISTA',
    'SC': 'FLORIANOPOLIS',
    'SP': 'SAO PAULO',
    'SE': 'ARACAJU',
    'TO': 'PALMAS'
}

def extrair_capitais():
    print("Lendo o arquivo CSV...")
    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8', low_memory=False)

    print("Filtrando contatos das capitais...")
    df['CIDADE_LIMPA'] = df['CIDADE'].astype(str).str.strip().str.upper()
    df['ESTADO_LIMPO'] = df['ESTADO'].astype(str).str.strip().str.upper()

    def eh_capital(row):
        uf = row['ESTADO_LIMPO']
        cidade = row['CIDADE_LIMPA']
        return capitais_map.get(uf) == cidade

    df_capitais = df[df.apply(eh_capital, axis=1)].copy()
    df_capitais.drop(columns=['CIDADE_LIMPA', 'ESTADO_LIMPO'], inplace=True)

    print(f"Total de contatos em capitais: {len(df_capitais)}")

    print(f"Gerando arquivo Excel multi-aba para capitais...")
    with pd.ExcelWriter(output_capitais_brain, engine='xlsxwriter') as writer:
        # Aba de Resumo
        resumo = df_capitais.groupby(['ESTADO', 'CIDADE']).size().reset_index(name='QUANTIDADE')
        resumo.to_excel(writer, sheet_name='RESUMO_CAPITAIS', index=False)
        
        # Uma aba para cada UF (filtramos apenas as que possuem capital no arquivo)
        for uf in sorted(df_capitais['ESTADO'].unique().astype(str)):
            print(f"  Criando aba de capital para {uf}...")
            df_uf_cap = df_capitais[df_capitais['ESTADO'] == uf]
            df_uf_cap.to_excel(writer, sheet_name=uf, index=False)

    # Copiar para o Desktop
    try:
        shutil.copy(output_capitais_brain, output_capitais_desktop)
        print(f"Arquivo de capitais (multi-aba) salvo em: {output_capitais_desktop}")
    except Exception as e:
        print(f"Erro ao copiar: {e}")

if __name__ == "__main__":
    if not os.path.exists(caminho_csv):
        print(f"Erro: Arquivo não encontrado.")
    else:
        extrair_capitais()
