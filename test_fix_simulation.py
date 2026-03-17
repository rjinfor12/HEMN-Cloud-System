import pandas as pd
import unicodedata

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_name(name):
    if not name: return ""
    name = remove_accents(str(name).upper().strip())
    suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR', ' SEGUNDO', ' TERCEIRO']
    for sfx in suffixes:
        if name.endswith(sfx):
            name = name[:-len(sfx)].strip()
            break
    return name

# Simulated Data
empresas = pd.DataFrame([
    {'cnpj_basico': '12345678', 'razao_social': 'ROGERIO TRANSPORTES LTDA'},
    {'cnpj_basico': '10890651', 'razao_social': 'FARMA POPULAR LTDA'}
])

socios = pd.DataFrame([
    {'cnpj_basico': '12345678', 'nome_socio': 'ROGERIO ELIAS DO NASCIMENTO JUNIOR', 'cnpj_cpf_socio': '***522794**'},
    {'cnpj_basico': '10890651', 'nome_socio': 'CAIO VINICIUS LOPES MORAIS', 'cnpj_cpf_socio': '***522794**'},
    {'cnpj_basico': '10890651', 'nome_socio': 'MARIA SILVA', 'cnpj_cpf_socio': '***111222**'}
])

estabelecimentos = pd.DataFrame([
    {'cnpj_basico': '12345678', 'cnpj_completo': '12345678000199', 'situacao': 'ATIVA'},
    {'cnpj_basico': '10890651', 'cnpj_completo': '10890651000100', 'situacao': 'ATIVA'}
])

def simulate_deep_search(search_name, search_cpf):
    print(f"\n--- Searching for: Name='{search_name}', CPF='{search_cpf}' ---")
    
    # Phase 1: Basics (Simplified)
    basics = []
    if search_cpf:
        cpf_clean = ''.join(filter(str.isdigit, str(search_cpf)))
        cpf_mask = f"***{cpf_clean[3:9]}**"
        basics.extend(socios[socios['cnpj_cpf_socio'] == cpf_mask]['cnpj_basico'].tolist())
    
    if search_name:
        name_norm = normalize_name(search_name)
        basics.extend(socios[socios['nome_socio'].str.contains(name_norm, na=False)]['cnpj_basico'].tolist())
        basics.extend(empresas[empresas['razao_social'].str.contains(name_norm, na=False)]['cnpj_basico'].tolist())
    
    basics = list(set(basics))
    print(f"Candidates (basics): {basics}")

    # Phase 2: Final Query with Fingerprint
    socio_filters = []
    if search_cpf:
        cpf_clean = ''.join(filter(str.isdigit, str(search_cpf)))
        cpf_mask = f"***{cpf_clean[3:9]}**"
        socio_filters.append(lambda s: s['cnpj_cpf_socio'] == cpf_mask)
    
    if search_name:
        name_norm = normalize_name(search_name)
        socio_filters.append(lambda s: name_norm in normalize_name(s['nome_socio']))
    
    def socio_match(s):
        if not socio_filters: return True
        return all(f(s) for f in socio_filters)

    company_name_match = lambda e: False
    if search_name:
        name_norm = normalize_name(search_name)
        company_name_match = lambda e: name_norm in normalize_name(e['razao_social'])

    # Join Simulation
    results = []
    for b in basics:
        e = empresas[empresas['cnpj_basico'] == b].iloc[0]
        est = estabelecimentos[estabelecimentos['cnpj_basico'] == b].iloc[0]
        s_list = socios[socios['cnpj_basico'] == b]
        
        # Apply the complex filter: (socio_match OR company_name_match)
        # In SQL: LEFT JOIN s ON ... WHERE ... AND (socio_match_sql OR company_name_match)
        
        has_any_match = False
        for _, s in s_list.iterrows():
            if socio_match(s) or company_name_match(e):
                results.append({
                    'razao_social': e['razao_social'],
                    'cnpj': est['cnpj_completo'],
                    'nome_socio': s['nome_socio'],
                    'cpf_socio': s['cnpj_cpf_socio']
                })
                has_any_match = True
        
        # Handling the case where no partners exist or match but company matches
        if not has_any_match and company_name_match(e):
             results.append({
                'razao_social': e['razao_social'],
                'cnpj': est['cnpj_completo'],
                'nome_socio': 'N/A',
                'cpf_socio': 'N/A'
            })

    return pd.DataFrame(results)

# Test 1: Search for Rogerio + his CPF -> Should NOT show Farma Popular
res1 = simulate_deep_search("ROGERIO ELIAS", "09752279473")
print(res1)

# Test 2: Search for Farma Popular (Company Name) -> Should show all partners
res2 = simulate_deep_search("FARMA POPULAR", None)
print(res2)

# Test 3: Search for Rogerio (Name only) -> Should show his companies AND Maria if name matches company
res3 = simulate_deep_search("ROGERIO", None)
print(res3)
