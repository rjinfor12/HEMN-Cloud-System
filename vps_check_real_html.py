import requests

url = "http://127.0.0.1:8000/areadocliente/"
try:
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    print("--- HTML CONTENT (FIRST 2000 CHARS) ---")
    print(response.text[:2000])
    print("\n--- HTML CONTENT (LAST 2000 CHARS) ---")
    print(response.text[-2000:])
    
    if "main.js" in response.text:
        print("\n!!! ENCONTRADO REFERÊNCIA A main.js NO HTML SERVIDO !!!")
    else:
        print("\nNÃO há referência a main.js no HTML servido.")
except Exception as e:
    print(f"Erro ao acessar backend local: {e}")
