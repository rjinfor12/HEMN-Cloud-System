import os

def search_in_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.html', '.js', '.css', '.txt')):
                path = os.path.join(root, file)
                try:
                    # Try different encodings
                    for enc in ['utf-8', 'latin-1', 'utf-16']:
                        try:
                            with open(path, 'r', encoding=enc) as f:
                                content = f.read()
                                if pattern in content:
                                    print(f"FOUND in {path} (encoding: {enc})")
                                    # Find matching lines
                                    lines = content.splitlines()
                                    for i, line in enumerate(lines):
                                        if pattern in line:
                                            print(f"  Line {i+1}: {line.strip()}")
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"Could not read {path}: {e}")

search_in_files(r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis', '90GB')
search_in_files(r'c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis', 'Pesquisando')
