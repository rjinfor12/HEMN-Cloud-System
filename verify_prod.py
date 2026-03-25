import requests
import json

base_url = "https://hemnsystem.com.br/areadocliente"
username = "admin" # Replace with real admin if known, or I'll just check if it exists
password = "admin" # I'll try common or just see if I can get a 401/403 vs 404

def test_endpoint():
    print(f"Testing {base_url}/me/db_version ...")
    try:
        # First attempt without token to see if it's there (should be 401/403, not 404)
        r = requests.get(f"{base_url}/me/db_version")
        print(f"Status Code (No Auth): {r.status_code}")
        if r.status_code == 404:
            print("ERROR: Endpoint NOT FOUND (404)")
        else:
            print("SUCCESS: Endpoint found (Auth required)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoint()
