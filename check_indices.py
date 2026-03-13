
import sqlite3

db_path = r"C:\HEMN_SYSTEM_DB\cnpj.db"

def check_indices():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['socios', 'empresas', 'estabelecimento']
        for table in tables:
            print(f"Indices for table: {table}")
            cursor.execute(f"PRAGMA index_list({table})")
            indices = cursor.fetchall()
            if not indices:
                print("  No indices found.")
            else:
                for idx in indices:
                    print(f"  - {idx[1]} (Unique: {idx[2]})")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_indices()
