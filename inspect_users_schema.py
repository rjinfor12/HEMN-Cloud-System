import sqlite3
import os

db_path = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\hemn_cloud.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Columns in 'users' table:")
for col in columns:
    print(col)

# Get some sample data to see how it's used
cursor.execute("SELECT * FROM users LIMIT 1")
first_row = cursor.fetchone()
if first_row:
    colnames = [description[0] for description in cursor.description]
    print("\nSample user data:")
    for name, value in zip(colnames, first_row):
        print(f"{name}: {value}")

conn.close()
