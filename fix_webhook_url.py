"""
Corrige a URL duplicada do webhook ASAAS e garante que está ativo.
"""
import requests
import json

ASAAS_API_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjEzMDJlNTFjLTgwODgtNGRmNi1iZTA3LWVkYmE0YzI5Y2UwYzo6JGFhY2hfODExNDEyNmEtZWI2Yy00OGFlLWI4OTktZjYyZjljMDdkNmIw"
ASAAS_URL = "https://www.asaas.com/api/v3"
WEBHOOK_ID = "092f13d1-a40f-4b4a-977c-06ac1d30af25"

# URL CORRETA do webhook
CORRECT_WEBHOOK_URL = "https://hemnsystem.com.br/areadocliente/webhook/asaas"

headers = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

print(f"Corrigindo URL do webhook para: {CORRECT_WEBHOOK_URL}")

payload = {
    "url": CORRECT_WEBHOOK_URL,
    "enabled": True,
    "interrupted": False,
    "events": ["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"]
}

r = requests.put(f"{ASAAS_URL}/webhooks/{WEBHOOK_ID}", json=payload, headers=headers)
print(f"Status: {r.status_code}")
result = r.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

if r.status_code == 200:
    print(f"\n[OK] URL corrigida para: {result.get('url')}")
    print(f"     interrupted: {result.get('interrupted')}")
    print(f"     enabled: {result.get('enabled')}")
else:
    print(f"\n[ERRO] Falha ao atualizar webhook: {r.text}")
