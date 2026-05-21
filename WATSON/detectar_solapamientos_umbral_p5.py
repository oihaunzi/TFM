import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

INPUT_CSV = "resultados_fingerprints_2d/fingerprints_interactivo_pca.csv"
OUT_DIR = "resultados_fingerprints_2d/solapamientos_p5"

THRESHOLD = 0.032791

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)
labels = sorted(df["label"].unique())

rows = []

for label_a, label_b in combinations(labels, 2):
    a = df[df["label"] == label_a][["x", "y"]].values
    b = df[df["label"] == label_b][["x", "y"]].values

    distances = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))

    min_dist = distances.min()

    if min_dist <= THRESHOLD:
        rows.append({
            "label_1": label_a,
            "label_2": label_b,
            "distancia_minima": min_dist,
            "threshold": THRESHOLD
        })

result = pd.DataFrame(rows)

if not result.empty:
    result = result.sort_values("distancia_minima", ascending=True)

pairs_csv = os.path.join(OUT_DIR, "pares_solapados_p5.csv")
result.to_csv(pairs_csv, index=False)

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

summary_csv = os.path.join(OUT_DIR, "resumen_solapamientos_p5.csv")
summary.to_csv(summary_csv, index=False)

txt_file = os.path.join(OUT_DIR, "resumen_solapamientos_p5.txt")

with open(txt_file, "w", encoding="utf-8") as f:
    f.write("RESUMEN DE SOLAPAMIENTOS CON UMBRAL P5\n")
    f.write("=====================================\n\n")
    f.write(f"Umbral utilizado: {THRESHOLD}\n")
    f.write(f"Labels/webs totales: {len(labels)}\n")
    f.write(f"Labels con solapamiento: {(summary['num_solapamientos'] > 0).sum()}\n")
    f.write(f"Labels sin solapamiento: {(summary['num_solapamientos'] == 0).sum()}\n")
    f.write(f"Pares solapados: {len(result)}\n")
    f.write(f"Pares posibles: {len(labels) * (len(labels) - 1) // 2}\n\n")

    f.write("TOP pares solapados:\n")
    f.write("--------------------\n")

    if result.empty:
        f.write("No se han detectado pares solapados.\n")
    else:
        for _, row in result.head(50).iterrows():
            f.write(
                f"{row['label_1']} <-> {row['label_2']} "
                f"distancia={row['distancia_minima']:.6f}\n"
            )

top = summary.head(30)

plt.figure(figsize=(18, 12))
plt.barh(top["label"], top["num_solapamientos"])
plt.xlabel("Número de solapamientos")
plt.ylabel("Web / label")
plt.title(f"Top 30 webs con más solapamientos PCA — umbral P5={THRESHOLD}")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "top_solapamientos_p5.png"), dpi=300)
plt.close()

print("Generado:")
print(pairs_csv)
print(summary_csv)
print(txt_file)
print(os.path.join(OUT_DIR, "top_solapamientos_p5.png"))

print("\nResumen:")
print(f"Umbral usado: {THRESHOLD}")
print(f"Labels/webs totales: {len(labels)}")
print(f"Labels con solapamiento: {(summary['num_solapamientos'] > 0).sum()}")
print(f"Labels sin solapamiento: {(summary['num_solapamientos'] == 0).sum()}")
print(f"Pares solapados: {len(result)}")
