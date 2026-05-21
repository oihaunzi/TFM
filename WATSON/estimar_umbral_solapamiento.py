import os
import pandas as pd
import numpy as np

INPUT_CSV = "resultados_fingerprints_2d/fingerprints_interactivo_pca.csv"
OUT_DIR = "resultados_fingerprints_2d/umbrales"

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)

labels = sorted(df["label"].unique())

intra_distances = []
inter_min_distances = []

# Distancias intra-clase: puntos de la misma web
for label in labels:
    points = df[df["label"] == label][["x", "y"]].values

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = np.linalg.norm(points[i] - points[j])
            intra_distances.append(d)

# Distancia mínima inter-clase por par de webs
for i, label_a in enumerate(labels):
    a = df[df["label"] == label_a][["x", "y"]].values

    for label_b in labels[i + 1:]:
        b = df[df["label"] == label_b][["x", "y"]].values

        distances = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
        inter_min_distances.append(distances.min())

intra = np.array(intra_distances)
inter_min = np.array(inter_min_distances)

def resumen(nombre, arr):
    return {
        "tipo": nombre,
        "n": len(arr),
        "min": np.min(arr),
        "p1": np.percentile(arr, 1),
        "p5": np.percentile(arr, 5),
        "p10": np.percentile(arr, 10),
        "p25": np.percentile(arr, 25),
        "media": np.mean(arr),
        "mediana": np.median(arr),
        "p75": np.percentile(arr, 75),
        "p90": np.percentile(arr, 90),
        "p95": np.percentile(arr, 95),
        "max": np.max(arr),
        "desv": np.std(arr),
    }

resumen_df = pd.DataFrame([
    resumen("intra_clase", intra),
    resumen("inter_clase_minima", inter_min),
])

resumen_df.to_csv(os.path.join(OUT_DIR, "resumen_umbrales.csv"), index=False)

print(resumen_df)

print("\nRecomendación:")
print("Umbral estricto  = percentil 1 de inter_clase_minima")
print("Umbral medio     = percentil 5 de inter_clase_minima")
print("Umbral laxo      = percentil 10 de inter_clase_minima")

print("\nValores recomendados:")
print(f"estricto: {np.percentile(inter_min, 1):.6f}")
print(f"medio:    {np.percentile(inter_min, 5):.6f}")
print(f"laxo:     {np.percentile(inter_min, 10):.6f}")
