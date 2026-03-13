
import requests
import json

url = 'http://127.0.0.1:8000/tasks/extract'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MzM3MDM5MX0.4V9-2mAN96MKVubrYWQKOxK8ZZBsv5i4nKYmLRDNDKY',
    'Content-Type': 'application/json'
}
payload = {
    'uf': 'CE',
    'cidade': 'FORTALEZA',
    'tipo_tel': 'TODOS',
    'situacao': '02'
}

r = requests.post(url, headers=headers, json=payload)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
