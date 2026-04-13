import sys
import traceback
import os

print("--- DIAGNOSTIC START ---")
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    print("Checking dependencies...")
    import fastapi
    import passlib
    import jwt
    import pandas
    
    print("Attempting to import HEMN_Cloud_Server...")
    import HEMN_Cloud_Server
    print("IMPORT SUCCESSFUL!")
    
except Exception:
    print("\n!!! CRITICAL ERROR DURING IMPORT !!!")
    traceback.print_exc()
    sys.exit(1)
