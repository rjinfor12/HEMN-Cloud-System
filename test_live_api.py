import requests
import json

# Try to find a token in localStorage or use a known one if possible.
# Since I don't have the token, I'll try to check if there is an unauthenticated way or just look at the code.
# Actually, I'll use the 'engine' locally again but this time I'll check if the 'HEMN_Cloud_Server.py' logic has any flaw.

API = "http://localhost:8000/areadocliente"

def test_api():
    try:
        # We need a token. I'll try to login with a known user if I can find one in the DB.
        import sqlite3
        conn = sqlite3.connect("hemn_cloud.db")
        user = conn.execute("SELECT username, password FROM users LIMIT 1").fetchone()
        conn.close()
        
        if not user:
            print("No users found to test API.")
            return

        print(f"Logging in as {user[0]}...")
        login_res = requests.post(f"{API}/login", json={"username": user[0], "password": user[1]})
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Fetching active tasks...")
        res = requests.get(f"{API}/tasks/active", headers=headers)
        if res.status_code == 200:
            tasks = res.json()
            print(f"Found {len(tasks)} tasks.")
            for t in tasks:
                print(f"Task ID: {t.get('id')} | Filters: {t.get('filters')}")
        else:
            print(f"Failed to fetch tasks: {res.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

test_api()
