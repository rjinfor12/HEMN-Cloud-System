import sqlite3
import os

DB_PATH = "/var/www/hemn_cloud/hemn_cloud.db"

def check_admin():
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    user = cursor.execute("SELECT username, role, status, password FROM users WHERE username = 'admin' COLLATE NOCASE").fetchone()
    if user:
        print(f"User found: {dict(user)}")
        # Check if password looks like pbkdf2
        pwd = user['password']
        if pwd.startswith('$pbkdf2-sha256$'):
            print("Password is pbkdf2-sha256")
        else:
            print(f"Password is NOT pbkdf2-sha256 (starts with {pwd[:10]})")
    else:
        print("User 'admin' NOT found")
    
    conn.close()

if __name__ == "__main__":
    check_admin()
