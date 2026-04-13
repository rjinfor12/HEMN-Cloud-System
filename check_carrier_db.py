
import sqlite3
import os

db_path = r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_carrier.db'

def check_db():
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("--- Table Info ---")
        cursor.execute("PRAGMA table_info(portabilidade)")
        for row in cursor.fetchall():
            print(row)
            
        print("\n--- Index Info ---")
        cursor.execute("PRAGMA index_list(portabilidade)")
        for row in cursor.fetchall():
            print(row)
            
        print("\n--- Query Plan ---")
        cursor.execute("EXPLAIN QUERY PLAN SELECT operadora_id FROM portabilidade WHERE telefone = '11999999999'")
        for row in cursor.fetchall():
            print(row)
            
        print("\n--- Sample Data ---")
        cursor.execute("SELECT * FROM portabilidade LIMIT 5")
        for row in cursor.fetchall():
            print(row)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
