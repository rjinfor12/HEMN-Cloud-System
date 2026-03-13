import sqlite3
import pandas as pd

db_path = r"C:\Users\Junior T.I\scratch\data_analysis\cnpj.db"

# Let's check a sample of the tables to see why left join is failing
try:
    conn = sqlite3.connect(db_path)
    print("Estabelecimento sample:")
    df_estab = pd.read_sql_query("SELECT cnpj_basico, cnae_fiscal, uf FROM estabelecimento LIMIT 5", conn)
    print(df_estab)
    
    print("\nEmpresas sample:")
    df_emp = pd.read_sql_query("SELECT cnpj_basico, razao_social FROM empresas LIMIT 5", conn)
    print(df_emp)
    
    # Try an inner join manually
    print("\nInner Join test:")
    query = """
    SELECT e.razao_social, estab.cnpj_basico 
    FROM estabelecimento estab 
    JOIN empresas e ON estab.cnpj_basico = e.cnpj_basico 
    LIMIT 5
    """
    df_join = pd.read_sql_query(query, conn)
    print(df_join)
    
    # Check types
    print("\nTypes:")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(estabelecimento)")
    print("Estabelecimento:", [row[1:3] for row in cur.fetchall() if row[1] == 'cnpj_basico'])
    cur.execute("PRAGMA table_info(empresas)")
    print("Empresas:", [row[1:3] for row in cur.fetchall() if row[1] == 'cnpj_basico'])
    conn.close()
except Exception as e:
    print(e)
