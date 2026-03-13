import os
import re

index_path = '/var/www/hemn_cloud/static/index.html'
if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
        # 1. moduleLabels structure
        m1 = re.search(r'const\s+moduleLabels\s*=', content)
        if m1:
            print("--- moduleLabels occurrence ---")
            print(content[m1.start():m1.start()+300])
            
        # 2. renderStatementTable full body
        m2 = re.search(r'renderStatementTable\s*\(\s*logs\s*\)\s*\{', content)
        if m2:
            print("\n--- renderStatementTable occurrence ---")
            # Encontrar o final da função buscando o próximo '},' ou similar
            print(content[m2.start():m2.start()+2000])
            
        # 3. Table Headers
        m3 = re.search(r'<table class="data-table" id="statement-table">', content)
        if m3:
            print("\n--- Table Headers occurrence ---")
            print(content[m3.start():m3.start()+500])
else:
    print(f"File not found: {index_path}")
