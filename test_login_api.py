import requests

url = "http://localhost:8000/login"
data = {"username": "admin", "password": "admin123"}

try:
    print(f"Testing login at {url}...")
    # Try as form data (what the frontend uses)
    response = requests.post(url, data=data)
    print(f"Status Code (Form): {response.status_code}")
    print(f"Response (Form): {response.text}")
    
    # Try as JSON
    response = requests.post(url, json=data)
    print(f"Status Code (JSON): {response.status_code}")
    print(f"Response (JSON): {response.text}")

except Exception as e:
    print(f"Error connecting to server: {e}")
