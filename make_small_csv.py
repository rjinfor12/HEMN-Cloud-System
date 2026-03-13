with open(r"C:\Users\Junior T.I\OneDrive\Área de Trabalho\sp.csv", "rb") as f_in:
    with open(r"C:\Users\Junior T.I\scratch\data_analysis\sp_small.csv", "wb") as f_out:
        for _ in range(200):
            line = f_in.readline()
            if not line: break
            f_out.write(line)
