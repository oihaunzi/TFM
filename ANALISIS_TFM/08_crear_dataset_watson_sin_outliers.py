import os
import glob
import shutil
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ORIGINAL_DIR = os.path.join(BASE_DIR, "..", "HOLMES", "20accesos_csv_label")
OUTLIERS_CSV = os.path.join(BASE_DIR, "resultados", "puntos_3d_H123_con_outliers.csv")

OUTPUT_DIR = os.path.join(BASE_DIR, "..", "HOLMES", "20accesos_csv_label_sin_outliers")
RESUMEN_OUTPUT = os.path.join(BASE_DIR, "resultados", "resumen_dataset_watson_sin_outliers.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(OUTLIERS_CSV)
df.columns = df.columns.str.strip()

# access_id que hay que eliminar por cada archivo
outliers_por_archivo = {}

for _, row in df[df["es_outlier"] == True].iterrows():
    archivo = row["archivo"]
    access_id = int(row["access_id"])

    if archivo not in outliers_por_archivo:
        outliers_por_archivo[archivo] = set()

    outliers_por_archivo[archivo].add(access_id)


resumen = []

csv_files = sorted(glob.glob(os.path.join(ORIGINAL_DIR, "*.csv")))

for file_path in csv_files:
    archivo = os.path.basename(file_path)
    output_path = os.path.join(OUTPUT_DIR, archivo)

    eliminar = outliers_por_archivo.get(archivo, set())

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lineas = [line.rstrip("\n") for line in f]

    nuevas_lineas = []
    access_id = 1
    i = 0
    eliminados = 0
    conservados = 0

    while i < len(lineas):
        linea = lineas[i]

        if ",H123-compact:" in linea and i + 1 < len(lineas):
            bloque_compact = lineas[i:i+2]

            # Buscar después el bloque H123
            if i + 3 < len(lineas) and ",H123:" in lineas[i+2]:
                bloque_h123 = lineas[i+2:i+4]

                if access_id not in eliminar:
                    nuevas_lineas.extend(bloque_compact)
                    nuevas_lineas.extend(bloque_h123)
                    conservados += 1
                else:
                    eliminados += 1

                access_id += 1
                i += 4
            else:
                nuevas_lineas.append(linea)
                i += 1
        else:
            nuevas_lineas.append(linea)
            i += 1

    with open(output_path, "w", encoding="utf-8") as f:
        for linea in nuevas_lineas:
            f.write(linea + "\n")

    resumen.append({
        "archivo": archivo,
        "accesos_originales": conservados + eliminados,
        "outliers_eliminados": eliminados,
        "accesos_restantes": conservados
    })

resumen_df = pd.DataFrame(resumen)
resumen_df.to_csv(RESUMEN_OUTPUT, index=False)

print("[OK] Dataset WATSON sin outliers creado en:")
print(OUTPUT_DIR)

print("\n[OK] Resumen guardado en:")
print(RESUMEN_OUTPUT)

print("\nResumen:")
print(resumen_df.describe())

print("\nMínimo de accesos restantes por URL:")
print(resumen_df["accesos_restantes"].min())
