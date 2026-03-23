import sqlite3
import os

db_path = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current columns to avoid duplicates
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "vencimento_dia" not in columns:
        print("Adding 'vencimento_dia' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN vencimento_dia INTEGER DEFAULT 10")
    
    if "valor_mensal" not in columns:
        print("Adding 'valor_mensal' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN valor_mensal REAL DEFAULT 0.0")
    
    # Set default valor_mensal for CLINICAS users if they don't have one
    print("Setting default valor_mensal for CLINICAS role...")
    cursor.execute("UPDATE users SET valor_mensal = 1099.0 WHERE role = 'CLINICAS' AND (valor_mensal IS NULL OR valor_mensal = 0.0)")
    
    conn.commit()
    print("Migration completed successfully.")

except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()

finally:
    conn.close()
