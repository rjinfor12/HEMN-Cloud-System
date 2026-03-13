"""
Reativa o webhook do ASAAS via API.
"""
import requests
import json

ASAAS_API_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjEzMDJlNTFjLTgwODgtNGRmNi1iZTA3LWVkYmE0YzI5Y2UwYzo6JGFhY2hfODExNDEyNmEtZWI2Yy00OGFlLWI4OTktZjYyZjljMDdkNmIw"
ASAAS_URL = "https://www.asaas.com/api/v3"

headers = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

# 1. Listar webhooks
print("=== Listando webhooks cadastrados ===")
r = requests.get(f"{ASAAS_URL}/webhooks", headers=headers)
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))

# 2. Para cada webhook pausado, reativar
webhooks = data.get("data", [])
for wh in webhooks:
    wh_id = wh.get("id")
    wh_name = wh.get("name", "")
    wh_enabled = wh.get("enabled", True)
    wh_interrupted = wh.get("interrupted", False)
    
    print(f"\n>>> Webhook: {wh_name} | ID: {wh_id} | enabled: {wh_enabled} | interrupted: {wh_interrupted}")
    
    if not wh_enabled or wh_interrupted:
        print(f"  Reativando webhook '{wh_name}'...")
        payload = {
            "enabled": True,
            "interrupted": False
        }
        r2 = requests.put(f"{ASAAS_URL}/webhooks/{wh_id}", json=payload, headers=headers)
        print(f"  Resposta: {r2.status_code}")
        print(f"  Body: {r2.text}")
    else:
        print(f"  Webhook ja esta ativo.")

print("\n=== Verificacao final ===")
r3 = requests.get(f"{ASAAS_URL}/webhooks", headers=headers)
final = r3.json()
for wh in final.get("data", []):
    print(f"  {wh.get('name')}: enabled={wh.get('enabled')}, interrupted={wh.get('interrupted')}")
