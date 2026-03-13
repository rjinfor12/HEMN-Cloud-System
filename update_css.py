import os

filepath = r"c:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\static\design-system.css"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """textarea:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgba(58, 123, 213, 0.12);
}"""

replacement = """textarea:focus {
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgba(58, 123, 213, 0.12);
}

select option {
    background-color: var(--bg-card);
    color: var(--text-1);
}"""

new_content = content.replace(target, replacement)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("CSS updated successfully!")
