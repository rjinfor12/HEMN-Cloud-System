import zipfile
import xml.etree.ElementTree as ET

# Verificando como o Excel salvou os dados brutos no arquivo
try:
    with zipfile.ZipFile(r"C:\Users\Junior T.I\.gemini\antigravity\scratch\data_analysis\test_split_out.xlsx", "r") as z:
        sheet = z.read("xl/worksheets/sheet1.xml")
        root = ET.fromstring(sheet)
        for row in root.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row")[:3]:
            print(f"Row {row.attrib.get('r')}:")
            for c in row.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                val = v.text if v is not None else "EMPTY"
                print(f"  Col {c.attrib.get('r')} - Type {c.attrib.get('t')}: {val}")
except Exception as e:
    print(e)
