import sqlite3
from passlib.context import CryptContext
import os

# Paths and Config
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"

def rehash_admin(password):
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    new_hash = pwd_context.hash(password)
    cursor.execute("UPDATE users SET password = ? WHERE username = 'admin' COLLATE NOCASE", (new_hash,))
    conn.commit()
    conn.close()
    print("Admin password re-hashed successfully using pbkdf2_sha256")

if __name__ == "__main__":
    rehash_admin("1304@Ev19")
