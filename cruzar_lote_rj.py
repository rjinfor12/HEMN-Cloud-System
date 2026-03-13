import pandas as pd
import sqlite3
import os
import time

# Configurações
db_path = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\cnpj.db"
input_file = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\cruzar\RJ.xlsx"
output_file = r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\RJ_Assertivo_Ativo_Completo.csv"

def cruzar_lote_assertivo():
    start_time = time.time()
    print("Iniciando cruzamento ASSERTIVO (Nome + CPF - 638k registros)...")
    
    # 1. Carregar Dados de Entrada
    print("Lendo RJ.xlsx...")
    df_rj = pd.read_excel(input_file)
    df_rj['NOME'] = df_rj['NOME'].astype(str).str.upper().str.strip()
    df_rj['CPF_STR'] = df_rj['CPF'].astype(str).str.zfill(11)
    # Extrair miolo do CPF (posições 4 a 9 - 123[456789]01)
    # No Excel index 0: 012[345678]910 -> Miolo é df['CPF_STR'].str[3:9]
    df_rj['MIOLO'] = df_rj['CPF_STR'].str[3:9]
    
    unique_names = df_rj['NOME'].unique().tolist()
    total_unique = len(unique_names)
    print(f"Total de nomes únicos: {total_unique}")
    
    # Mapa: Nome -> Lista de tuples (cnpj_basico, cpf_mascarado)
    cnpj_map = {} 
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 2. Processar nomes em lotes para identificar CNPJs e suas máscaras de CPF
        batch_size = 500
        for i in range(0, total_unique, batch_size):
            batch = unique_names[i:i+batch_size]
            placeholders = ",".join(["?"] * len(batch))
            
            if (i % 50000) == 0:
                print(f"Buscando nomes na base: {i} de {total_unique}...")
            
            # Busca em Sócios (pegando a máscara do CPF)
            query_socios = f"SELECT nome_socio, cnpj_basico, cnpj_cpf_socio FROM socios WHERE nome_socio IN ({placeholders})"
            cursor.execute(query_socios, batch)
            rows = cursor.fetchall()
            for name, cnpj, mask in rows:
                if name not in cnpj_map: cnpj_map[name] = []
                cnpj_map[name].append({'cnpj': cnpj, 'mask': str(mask)})

            # Busca em Empresas (MEIs)
            query_empRes = f"SELECT razao_social, cnpj_basico FROM empresas WHERE razao_social IN ({placeholders})"
            cursor.execute(query_empRes, batch)
            rows = cursor.fetchall()
            for name, cnpj in rows:
                if name not in cnpj_map: cnpj_map[name] = []
                # Para MEIs, o CPF está na própria Razão Social (name)
                cnpj_map[name].append({'cnpj': cnpj, 'mask': name})
        
        # 3. Filtrar e selecionar apenas CNPJs que batem com o Miolo do CPF do Excel
        print("Validando assertividade por miolo de CPF...")
        validated_cnpjs = set()
        
        # Inverter a lógica para buscar detalhes de estabelecimento apenas para quem passou no filtro
        name_to_valid_cnpjs = {} # Nome -> Set of CNPJs
        
        for index, row in df_rj.iterrows():
            nome = row['NOME']
            miolo = row['MIOLO']
            
            if nome in cnpj_map:
                for entry in cnpj_map[nome]:
                    mask = entry['mask']
                    # Validação: o miolo deve estar contido na máscara (socios) ou na razão social (MEI)
                    if miolo in mask:
                        if nome not in name_to_valid_cnpjs: name_to_valid_cnpjs[nome] = set()
                        name_to_valid_cnpjs[nome].add(entry['cnpj'])
                        validated_cnpjs.add(entry['cnpj'])
        
        print(f"Encontrados {len(validated_cnpjs)} CNPJs validados. Buscando detalhes ATIVOS...")
        
        # 4. Detalhes dos estabelecimentos (Apenas ATIVOS e 14 dígitos)
        validated_cnpjs_list = list(validated_cnpjs)
        detalhes_map = {}
        for i in range(0, len(validated_cnpjs_list), batch_size):
            batch = validated_cnpjs_list[i:i+batch_size]
            placeholders = ",".join(["?"] * len(batch))
            query_detalhes = f"""
            SELECT est.cnpj_basico, emp.razao_social, est.situacao_cadastral, est.uf, est.municipio, est.ddd1, est.telefone1, est.cnpj_ordem, est.cnpj_dv
            FROM estabelecimento est 
            JOIN empresas emp ON est.cnpj_basico = emp.cnpj_basico 
            WHERE est.situacao_cadastral = '02' 
              AND est.cnpj_basico IN ({placeholders})
            """
            cursor.execute(query_detalhes, batch)
            rows = cursor.fetchall()
            for r in rows:
                cnpj_c = str(r[0]).zfill(8) + str(r[7]).zfill(4) + str(r[8]).zfill(2)
                detalhes_map[r[0]] = {
                    'CNPJ_COMPLETO': cnpj_c, 
                    'RAZAO_SOCIAL': r[1], 
                    'UF': r[3], 
                    'MUNICIPIO': r[4], 
                    'TELEFONE': f"({r[5]}) {r[6]}" if r[5] and r[6] else ''
                }
        
        conn.close()
        
        # 5. Exportação final
        print("Exportando resultados assertivos para CSV...")
        first = True
        total_final = 0
        chunk_size = 50000
        
        for i in range(0, len(df_rj), chunk_size):
            chunk_rj = df_rj.iloc[i:i+chunk_size]
            chunk_results = []
            
            for index, row in chunk_rj.iterrows():
                nome = row['NOME']
                if nome in name_to_valid_cnpjs:
                    for cnpj_b in name_to_valid_cnpjs[nome]:
                        if cnpj_b in detalhes_map:
                            new_row = row.drop(['MIOLO', 'CPF_STR']).to_dict()
                            new_row.update(detalhes_map[cnpj_b])
                            new_row['ASSERTIVIDADE'] = 'ALTA (NOME+CPF)'
                            chunk_results.append(new_row)
                            total_final += 1
            
            if chunk_results:
                pd.DataFrame(chunk_results).to_csv(output_file, index=False, mode='w' if first else 'a', header=first, sep=';', encoding='utf-8-sig')
                first = False
                
        print(f"Sucesso! Salvo em: {output_file}")
        print(f"Total de registros assertivos ativos: {total_final}")
        print(f"Tempo total: {time.time() - start_time:.2f} segundos.")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    cruzar_lote_assertivo()
