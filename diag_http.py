import requests

url = "http://129.121.45.136:8123/"
headers = {
    "X-ClickHouse-User": "hemn",
    "X-ClickHouse-Key": "HeMNSecurePassword2024!"
}

query = "SELECT s.nome_socio, s.cnpj_cpf_socio, e.razao_social, e.cnpj_basico FROM hemn.socios s JOIN hemn.empresas e ON s.cnpj_basico = e.cnpj_basico WHERE s.cnpj_cpf_socio = '***522794**' LIMIT 10 FORMAT JSONEachRow"

response = requests.post(url, headers=headers, data=query.encode('utf-8'))

if response.status_code == 200:
    for line in response.text.strip().split('\n'):
        print(line)
else:
    print(f"Error {response.status_code}: {response.text}")
