import pandas as pd

suffixes = ['JUNIOR', 'FILHO', 'NETO', 'SOBRINHO', 'JR']

def validate_match(name, row_name, cpf_digits, row_cpf):
    # Simplificado para o teste
    name = name.upper()
    row_name = row_name.upper()
    
    if cpf_digits and str(row_cpf) == cpf_digits:
        return True
    
    for sfx in suffixes:
        has_sfx_search = sfx in name
        has_sfx_result = sfx in row_name
        if has_sfx_search != has_sfx_result:
            print(f"Rejeitado por sufixo: {sfx} (Search: {has_sfx_search}, Result: {has_sfx_result})")
            return False 
    
    return True

print("--- Teste 1: JUNIOR vs JR ---")
# Se eu busco JUNIOR e o DB tem JR
# search tem 'JUNIOR' (True) e 'JR' (True, pois JR está dentro de JUNIOR)
# result tem 'JR' (True) e 'JUNIOR' (False) -> REJEITA
print(f"Match JUNIOR vs JR: {validate_match('ROGERIO JUNIOR', 'ROGERIO JR', '123', '***123**')}")

print("\n--- Teste 2: JR vs JUNIOR ---")
# Se eu busco JR e o DB tem JUNIOR
# search tem 'JR' (True) e 'JUNIOR' (False)
# result tem 'JR' (True) e 'JUNIOR' (True) -> REJEITA
print(f"Match JR vs JUNIOR: {validate_match('ROGERIO JR', 'ROGERIO JUNIOR', '123', '***123**')}")
