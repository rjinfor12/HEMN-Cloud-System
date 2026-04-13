from passlib.context import CryptContext
import sqlite3
import os

def reset_admin():
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    new_hash = pwd_context.hash("hemn123")
    DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = ? WHERE username = 'admin' COLLATE NOCASE", (new_hash,))
        if cur.rowcount == 0:
            print("Error: Admin user not found in database.")
        else:
            conn.commit()
            print("PASSWORD_RESET_SUCCESSFUL")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_admin()
