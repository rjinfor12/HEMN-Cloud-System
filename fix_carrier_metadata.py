import sqlite3
from datetime import datetime

db_path = "hemn_cloud.db"
conn = sqlite3.connect(db_path)
now_iso = datetime.utcnow().isoformat()

print(f"Forcing last_carrier_vps_timestamp to {now_iso} (UTC)")
conn.execute("INSERT OR REPLACE INTO system_metadata (key, value) VALUES ('last_carrier_vps_timestamp', ?)", (now_iso,))
conn.commit()

# Verify
cursor = conn.cursor()
cursor.execute("SELECT key, value FROM system_metadata WHERE key LIKE 'last_carrier_%'")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("Done.")
