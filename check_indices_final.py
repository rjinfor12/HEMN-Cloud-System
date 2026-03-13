import sqlite3
def check_indices():
    conn = sqlite3.connect('C:/HEMN_SYSTEM_DB/cnpj.db')
    cursor = conn.cursor()
    print("Indices na tabela 'socios':")
    for row in cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='socios'"):
        print(row)
    
    print("\nIndices na tabela 'estabelecimento':")
    for row in cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='estabelecimento'"):
        print(row)
        
    print("\nIndices na tabela 'empresas':")
    for row in cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='empresas'"):
        print(row)
    conn.close()

if __name__ == "__main__":
    check_indices()
