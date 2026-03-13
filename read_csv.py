with open(r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv", "r", encoding="utf-8", errors="replace") as f:
    for _ in range(5):
        print(repr(f.readline()))
