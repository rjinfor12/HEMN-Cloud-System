import paramiko
import time

# Contabo info
ip = "86.48.17.194"
user = "root"
pw = "^QP67kXax9AyuvF%"

def apply_projections():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pw, timeout=20)
        
        # 1. Estabelecimento Geo Projection
        print("Creating Geo Projection on estabelecimento...")
        client.exec_command("clickhouse-client --query \"ALTER TABLE hemn.estabelecimento ADD PROJECTION geo_idx (SELECT * ORDER BY uf, municipio)\"")
        time.sleep(2)
        print("Materializing Geo Projection (this runs in background)...")
        client.exec_command("clickhouse-client --query \"ALTER TABLE hemn.estabelecimento MATERIALIZE PROJECTION geo_idx\"")
        
        # 2. Empresas Join Projection
        print("Creating Join Projection on empresas...")
        client.exec_command("clickhouse-client --query \"ALTER TABLE hemn.empresas ADD PROJECTION join_idx (SELECT * ORDER BY cnpj_basico)\"")
        time.sleep(2)
        print("Materializing Join Projection (this runs in background)...")
        client.exec_command("clickhouse-client --query \"ALTER TABLE hemn.empresas MATERIALIZE PROJECTION join_idx\"")
        
        client.close()
        print("Projection commands sent successfully.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    apply_projections()
