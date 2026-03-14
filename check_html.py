import os

def check_html(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Checking {filename}...")
    
    # Check for basic tags presence
    tags = ['module-active', 'module-clinicas', 'nav-clinicas', 'runClinicasSearch']
    for t in tags:
        if t in content:
            print(f"Found: {t}")
        else:
            print(f"NOT FOUND: {t}")
            
    # Check for unclosed divs (rough check)
    opens = content.count('<div')
    closes = content.count('</div')
    print(f"Divs: Open={opens}, Close={closes}")
    
    # Check for sections
    s_opens = content.count('<section')
    s_closes = content.count('</section')
    print(f"Sections: Open={s_opens}, Close={s_closes}")

if __name__ == "__main__":
    check_html('index_vps.html')
