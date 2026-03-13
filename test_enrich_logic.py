import sys
import os
import pandas as pd
from cloud_engine import CloudEngine, remove_accents

def test_parsing():
    engine = CloudEngine("mock.db", "mock_carrier.db")
    
    # Mock database row (Establishing format from deep_enrich query)
    hit = {
        'razao_social': 'HEMN TECNOLOGIA LTDA',
        'cnpj_basico': '12345678', 'cnpj_ordem': '0001', 'cnpj_dv': '99',
        'situacao_cadastral': '02', 'uf': 'PR', 'municipio_nome': 'CURITIBA',
        'ddd1': '41', 'telefone1': '999998888',
        'ddd2': '41', 'telefone2': '33332222',
        'correio_eletronico': 'contato@hemn.com',
        'tipo_logradouro': 'RUA', 'logradouro': 'DAS FLORES',
        'numero': '123', 'complemento': 'APTO 1', 'bairro': 'CENTRO', 'cep': '80000000',
        'cnae_fiscal': '6201501', 'municipio': '12345'
    }
    
    # Test Address Parsing
    addr = engine._parse_address_columns(hit)
    print(f"Address Test: {addr.tolist()}")
    assert addr[0] == "RUA DAS FLORES"
    assert addr[4] == "CURITIBA"
    
    # Test Contact Parsing (CELULAR Priority)
    cont = engine._parse_contact_columns(hit, tipo_filtro="CELULAR")
    print(f"Contact Test (CELULAR): {cont.tolist()}")
    assert cont[1] == "999998888"
    assert cont[2] == "CELULAR"
    
    # Test Contact Parsing (FIXO Priority)
    cont_fixo = engine._parse_contact_columns(hit, tipo_filtro="FIXO")
    print(f"Contact Test (FIXO): {cont_fixo.tolist()}")
    assert cont_fixo[1] == "33332222"
    assert cont_fixo[2] == "FIXO"

    # Test Suffix Handling
    name = "JOSE DA SILVA JUNIOR"
    suffixes = [' JUNIOR', ' FILHO', ' NETO', ' SOBRINHO', ' JR']
    base_n = name
    for sfx in suffixes:
        if base_n.endswith(sfx):
            base_n = base_n[:-len(sfx)].strip()
            break
    print(f"Suffix Test: {name} -> {base_n}")
    assert base_n == "JOSE DA SILVA"

    print("\nSUCCESS: TODOS OS TESTES DE LOGICA PASSARAM!")

if __name__ == "__main__":
    try:
        test_parsing()
    except Exception as e:
        print(f"ERROR NO TESTE: {e}")
        sys.exit(1)
