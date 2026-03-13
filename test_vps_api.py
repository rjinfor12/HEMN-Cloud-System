import requests
import json

VPS_IP = "129.121.45.136"
API = f"http://{VPS_IP}/areadocliente"

def test_vps_api():
    try:
        # I'll try to check /tasks/active if it's open or just see if the endpoint responds.
        # Since I don't have a valid login for the VPS (passwords might be different),
        # I'll just check if the /me endpoint or similar is reachable (it will probably return 401).
        
        print(f"Checking VPS API at {API}...")
        res = requests.get(f"{API}/me")
        print(f"Status Code: {res.status_code}")
        if res.status_code == 401:
            print("VPS API is UP (401 Unauthorized as expected).")
        else:
            print(f"VPS API responded with: {res.status_code}")
            
    except Exception as e:
        print(f"Error testing VPS API: {e}")

test_vps_api()
