import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

INPUT_CSV = "resultados_fingerprints_2d/fingerprints_interactivo_pca.csv"
OUT_DIR = "resultados_fingerprints_2d/solapamientos_umbral_minimo"

THRESHOLD = 0.0005124365557144325

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)
labels = sorted(df["label"].unique())

rows = []
all_pairs = []

for label_a, label_b in combinations(labels, 2):
    a = df[df["label"] == label_a][["x", "y"]].values
    b = df[df["label"] == label_b][["x", "y"]].values

    distances = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    min_dist = float(distances.min())

    all_pairs.append({
        "label_1": label_a,
        "label_2": label_b,
        "distancia_minima": min_dist
    })

    if min_dist <= THRESHOLD:
        rows.append({
            "label_1": label_a,
            "label_2": label_b,
            "distancia_minima": min_dist,
            "threshold": THRESHOLD
        })

result = pd.DataFrame(rows).sort_values("distancia_minima")
all_pairs_df = pd.DataFrame(all_pairs).sort_values("distancia_minima")

pairs_csv = os.path.join(OUT_DIR, "pares_solapados_umbral_minimo.csv")
all_csv = os.path.join(OUT_DIR, "todos_los_pares_ordenados.csv")
summary_csv = os.path.join(OUT_DIR, "resumen_umbral_minimo.csv")
txt_file = os.path.join(OUT_DIR, "resumen_umbral_minimo.txt")
png_file = os.path.join(OUT_DIR, "top30_pares_mas_cercanos.png")

result.to_csv(pairs_csv, index=False)
all_pairs_df.to_csv(all_csv, index=False)

counts = {label: 0 for label in labels}

for _, row in result.iterrows():
    counts[row["label_1"]] += 1
    counts[row["label_2"]] += 1

summary = pd.DataFrame([
    {
        "label": label,
        "num_solapamientos": counts[label],
        "solapa": "si" if counts[label] > 0 else "no"
    }
    for label in labels
]).sort_values("num_solapamientos", ascending=False)

summary.to_csv(summary_csv, index=False)

with open(txt_file, "w", encoding="utf-8") as f:
    f.write("SOLAPAMIENTOS CON UMBRAL MÍNIMO INTER-CLASE NO NULO\n")
    f.write("===================================================\n\n")
    f.write(f"Umbral utilizado: {THRESHOLD}\n")
    f.write(f"Labels/webs totales: {len(labels)}\n")
    f.write(f"Labels con solapamiento: {(summary['num_solapamientos'] > 0).sum()}\n")
    f.write(f"Labels sin solapamiento: {(summary['num_solapamientos'] == 0).sum()}\n")
    f.write(f"Pares solapados: {len(result)}\n")
    f.write(f"Pares posibles: {len(labels) * (len(labels) - 1) // 2}\n\n")

    f.write("Pares considerados solapados:\n")
    f.write("-----------------------------\n")

    if result.empty:
        f.write("No se han detectado pares con este umbral.\n")
    else:
        for _, row in result.iterrows():
            f.write(
                f"{row['label_1']} <-> {row['label_2']} "
                f"distancia={row['distancia_minima']:.12f}\n"
            )

    f.write("\nTOP 30 pares más cercanos del dataset:\n")
    f.write("-------------------------------------\n")

    for _, row in all_pairs_df.head(30).iterrows():
        f.write(
            f"{row['label_1']} <-> {row['label_2']} "
            f"distancia={row['distancia_minima']:.12f}\n"
        )

top = all_pairs_df.head(30).copy()
top["pair"] = top["label_1"] + " <-> " + top["label_2"]

plt.figure(figsize=(20, 12))
plt.barh(top["pair"], top["distancia_minima"])
plt.axvline(THRESHOLD, linestyle="--", linewidth=2)
plt.xlabel("Distancia mínima PCA entre fingerprints")
plt.ylabel("Par de webs")
plt.title(f"Top 30 pares más cercanos — umbral={THRESHOLD}")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(png_file, dpi=300)
plt.close()

print("Generado:")
print(pairs_csv)
print(all_csv)
print(summary_csv)
print(txt_file)
print(png_file)

print("\nResumen:")
print(f"Umbral usado: {THRESHOLD}")
print(f"Labels/webs totales: {len(labels)}")
print(f"Labels con solapamiento: {(summary['num_solapamientos'] > 0).sum()}")
print(f"Labels sin solapamiento: {(summary['num_solapamientos'] == 0).sum()}")
print(f"Pares solapados: {len(result)}")

print("\nPares solapados:")
if result.empty:
    print("Ninguno")
else:
    print(result.to_string(index=False))
