
import sqlite3
from cloud_engine import CloudEngine
import os

# Simular ambiente Linux para usar os paths corretos ou passar kwargs
engine = CloudEngine(db_carrier_path="hemn_carrier.db", db_path="hemn_cloud.db")

print("--- Testando get_carrier_status ---")
status = engine.get_carrier_status()
print(f"Status inicial: {status}")

# Simular que a última atualização local foi antiga
conn = sqlite3.connect('hemn_cloud.db')
conn.execute("INSERT OR REPLACE INTO system_metadata (key, value) VALUES ('last_carrier_vps_timestamp', '2026-03-20T00:00:00')")
conn.commit()
conn.close()

print("\n--- Testando após simular base local antiga ---")
status = engine.get_carrier_status()
print(f"Status após simulação: {status}")
print(f"Update disponível: {status.get('update_available')}")
