import re
import os

with open('index_vps.html', 'r', encoding='utf-8') as f:
    html = f.read()

pattern = re.compile(r'<script>(.*?)</script>', re.DOTALL)
scripts = pattern.findall(html)

for i, script in enumerate(scripts):
    with open(f'test_script_{i}.js', 'w', encoding='utf-8') as sf:
        sf.write(script)

print(f"Extracted {len(scripts)} script blocks.")
