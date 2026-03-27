import sys
import os
import re

# Mocking parts of CloudEngine to test the CNAE logic
class MockCloudEngine:
    def test_cnae_logic(self, cnae_input):
        estab_conds = []
        params = {}
        filters = {"cnae": cnae_input}
        
        if filters.get("cnae"): 
            # Logic from cloud_engine.py
            raw_cnae = filters["cnae"].replace(';', ',')
            cnae_list = [c.strip() for c in raw_cnae.split(',') if c.strip()]
            
            if cnae_list:
                cnae_clauses = []
                for i, c_prefix in enumerate(cnae_list):
                    p_name = f"cnae_pref_{i}"
                    cnae_clauses.append(f"startsWith(estab_inner.cnae_fiscal, %({p_name})s)")
                    params[p_name] = c_prefix
                
                estab_conds.append(f"({' OR '.join(cnae_clauses)})")
        
        return estab_conds, params

engine = MockCloudEngine()

# Test 1: Single CNAE
conds, params = engine.test_cnae_logic("4711")
print(f"Test 1 (Single): {conds} | {params}")
assert conds == ["(startsWith(estab_inner.cnae_fiscal, %(cnae_pref_0)s))"]
assert params == {"cnae_pref_0": "4711"}

# Test 2: Multiple with comma
conds, params = engine.test_cnae_logic("4711, 4712")
print(f"Test 2 (Comma): {conds} | {params}")
assert conds == ["(startsWith(estab_inner.cnae_fiscal, %(cnae_pref_0)s) OR startsWith(estab_inner.cnae_fiscal, %(cnae_pref_1)s))"]
assert params == {"cnae_pref_0": "4711", "cnae_pref_1": "4712"}

# Test 3: Multiple with semicolon and mixed
conds, params = engine.test_cnae_logic("4711; 4712,4713")
print(f"Test 3 (Mixed): {conds} | {params}")
assert conds == ["(startsWith(estab_inner.cnae_fiscal, %(cnae_pref_0)s) OR startsWith(estab_inner.cnae_fiscal, %(cnae_pref_1)s) OR startsWith(estab_inner.cnae_fiscal, %(cnae_pref_2)s))"]
assert params == {"cnae_pref_0": "4711", "cnae_pref_1": "4712", "cnae_pref_2": "4713"}

print("All logic tests passed!")
