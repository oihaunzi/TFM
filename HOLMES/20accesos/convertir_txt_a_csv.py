import os
import csv

carpeta_txt = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/HOLMES/20accesos"
carpeta_csv = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/HOLMES/20accesos_csv"

os.makedirs(carpeta_csv, exist_ok=True)

for archivo in os.listdir(carpeta_txt):
    if archivo.endswith(".txt"):
        ruta_txt = os.path.join(carpeta_txt, archivo)
        nombre_base = os.path.splitext(archivo)[0]
        ruta_csv = os.path.join(carpeta_csv, nombre_base + ".csv")

        h1 = ""
        h2 = ""
        h3 = ""

        with open(ruta_txt, "r", encoding="utf-8", errors="ignore") as f:
            for linea in f:
                linea = linea.strip()

                if linea.startswith("H1"):
                    h1 = linea.split(":", 1)[1].strip()

                elif linea.startswith("H2"):
                    h2 = linea.split(":", 1)[1].strip()

                elif linea.startswith("H3"):
                    h3 = linea.split(":", 1)[1].strip()

        with open(ruta_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["sample", "H1", "H2", "H3"])
            writer.writerow([nombre_base, h1, h2, h3])

print("Conversión completada.")
