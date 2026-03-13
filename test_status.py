import requests
import sys

def test_task_status(tid):
    url = f"http://localhost:8000/tasks/{tid}"
    # No auth needed for this simple test if we mock the db
    print(f"Testing status for task: {tid}")
    try:
        # Mocking the GET request without actual auth to see if uvicorn logs the attempt or if it fails serialization
        # Wait, the endpoint has Depends(get_current_user), so it WILL fail 401 without token.
        # But uvicorn logs will show the 401.
        resp = requests.get(url)
        print(f"Response Code: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else "test-123"
    test_task_status(tid)
