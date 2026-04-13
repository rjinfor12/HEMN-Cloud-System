import requests
import json
import time

def trigger_recife():
    # Login to get session/token (we use basic auth or admin/hemn123)
    login_url = "https://hemnsystem.com.br/areadocliente/admin/auth/login"
    extract_url = "https://hemnsystem.com.br/areadocliente/extraction/start"
    status_url = "https://hemnsystem.com.br/areadocliente/tasks/state/active"
    
    # We'll use the already established credentials
    auth = ("admin", "hemn123")
    
    data = {
        "module": "TITANIUM",
        "filters": {
            "uf": "PE",
            "cidade": "RECIFE",
            "situacao": "02", # Ativas
            "perfil": "TODOS",
            "tipo_tel": "TODOS"
        }
    }
    
    print(f"Triggering search for Recife...")
    r = requests.post(extract_url, json=data, auth=auth)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
    
    if r.status_code == 200:
        tid = r.json().get("task_id")
        print(f"Task ID: {tid}")
        
        # Wait a few seconds for it to run
        for i in range(10):
            time.sleep(2)
            rs = requests.get(status_url, auth=auth)
            print(f"Polling: {rs.text}")
            if tid not in rs.text:
                print("Task finished or moved to history.")
                break

if __name__ == "__main__":
    trigger_recife()
