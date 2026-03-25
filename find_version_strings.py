import os

root_dir = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis"
targets = ["HEMN-V143", "V1.0.3", "UIFIX-GOLD"]

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(('.html', '.js', '.py', '.txt', '.css')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for target in targets:
                        if target in content:
                            print(f"FOUND {target} in {path}")
            except Exception as e:
                print(f"Error reading {path}: {e}")
