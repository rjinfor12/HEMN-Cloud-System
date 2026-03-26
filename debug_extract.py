import tarfile
import os
import shutil

local_zip = "/var/www/hemn_cloud/portabilidade.tar.bz2"
extract_path = "/tmp/test_extract"

if os.path.exists(extract_path):
    shutil.rmtree(extract_path)
os.makedirs(extract_path)

try:
    print(f"Checking file: {local_zip}")
    if not os.path.exists(local_zip):
        print("File does not exist!")
    else:
        print(f"Size: {os.path.getsize(local_zip)} bytes")
        
        print("Opening with tarfile.open(r:bz2)...")
        with tarfile.open(local_zip, "r:bz2") as tar:
            names = tar.getnames()
            print(f"Found {len(names)} members.")
            print(f"First 5: {names[:5]}")
            
            print("Extracting all to /tmp/test_extract...")
            tar.extractall(path=extract_path)
            print("Success!")
            
except Exception as e:
    print(f"Error during extraction: {e}")
    import traceback
    traceback.print_exc()
