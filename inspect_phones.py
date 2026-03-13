import sqlite3
import pandas as pd

DB_PATH = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def inspect_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Pegar 50 registros de Natal (1761)
    q = """
        SELECT estab.cnpj_basico, estab.ddd1, estab.telefone1, estab.ddd2, estab.telefone2, e.razao_social
        FROM estabelecimento estab
        JOIN empresas e ON estab.cnpj_basico = e.cnpj_basico
        WHERE estab.municipio = '1761' AND estab.situacao_cadastral = '02'
        LIMIT 50
    """
    df = pd.read_sql_query(q, conn)
    print("Primeiros 50 registros com JOIN empresas:")
    print(df.head(20))
    
    # Verificar tipos e presença de telefone
    has_tel1 = df['telefone1'].notnull().sum()
    has_tel2 = df['telefone2'].notnull().sum()
    print(f"\nRegistros com Telefone 1: {has_tel1}/50")
    print(f"Registros com Telefone 2: {has_tel2}/50")
    
    if has_tel1 > 0:
        print("\nExemplos de Telefone 1:")
        print(df[df['telefone1'].notnull()]['telefone1'].head(10).tolist())
        
        # Testar a lógica do check_tel
        def check_tel(t):
            if not t or len(str(t).strip()) < 8: return None
            t = str(t).strip()
            return "CELULAR" if t[0] in '6789' or len(t)==9 else "FIXO"
            
        df['tipo'] = df['telefone1'].apply(check_tel)
        print("\nClassificação dos telefones:")
        print(df['tipo'].value_counts())

    conn.close()

if __name__ == "__main__":
    inspect_data()
