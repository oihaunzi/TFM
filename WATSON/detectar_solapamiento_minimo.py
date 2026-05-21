import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

INPUT_CSV = "resultados_fingerprints_2d/fingerprints_interactivo_pca.csv"
OUT_DIR = "resultados_fingerprints_2d/solapamientos_minimo"

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)
labels = sorted(df["label"].unique())

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

all_df = pd.DataFrame(all_pairs).sort_values("distancia_minima")

all_df.to_csv(os.path.join(OUT_DIR, "todos_los_pares_ordenados.csv"), index=False)

# Umbral mínimo no cero
non_zero = all_df[all_df["distancia_minima"] > 0]

THRESHOLD = float(non_zero.iloc[0]["distancia_minima"])

print(f"Umbral mínimo no cero detectado: {THRESHOLD}")

result = all_df[all_df["distancia_minima"] <= THRESHOLD].copy()

result.to_csv(os.path.join(OUT_DIR, "pares_mas_parecidos.csv"), index=False)

counts = {label: 0 for label in labels}

for _, row in result.iterrows():
    counts[row["label_1"]] += 1
    counts[row["label_2"]] += 1

summary = pd.DataFrame([
    {
        "label": label,
        "num_coincidencias_minimas": counts[label],
        "coincide": "si" if counts[label] > 0 else "no"
    }
    for label in labels
]).sort_values("num_coincidencias_minimas", ascending=False)

summary.to_csv(os.path.join(OUT_DIR, "resumen_minimo.csv"), index=False)

with open(os.path.join(OUT_DIR, "resumen_minimo.txt"), "w", encoding="utf-8") as f:
    f.write("SOLAPAMIENTO MÁS ESTRICTO POSIBLE\n")
    f.write("=================================\n\n")
    f.write(f"Umbral utilizado: {THRESHOLD}\n")
    f.write(f"Labels/webs totales: {len(labels)}\n")
    f.write(f"Pares detectados con ese umbral: {len(result)}\n\n")
    f.write("Pares más parecidos:\n")
    f.write("--------------------\n")

    for _, row in result.iterrows():
        f.write(
            f"{row['label_1']} <-> {row['label_2']} "
            f"distancia={row['distancia_minima']:.10f}\n"
        )

# gráfico solo de los 30 pares más cercanos
top = all_df.head(30).copy()
top["pair"] = top["label_1"] + " <-> " + top["label_2"]

plt.figure(figsize=(18, 12))
plt.barh(top["pair"], top["distancia_minima"])
plt.xlabel("Distancia mínima PCA entre fingerprints")
plt.ylabel("Par de webs")
plt.title("Top 30 pares de fingerprints más cercanos")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "top30_pares_mas_cercanos.png"), dpi=300)
plt.close()

print("Generado:")
print(os.path.join(OUT_DIR, "todos_los_pares_ordenados.csv"))
print(os.path.join(OUT_DIR, "pares_mas_parecidos.csv"))
print(os.path.join(OUT_DIR, "resumen_minimo.csv"))
print(os.path.join(OUT_DIR, "resumen_minimo.txt"))
print(os.path.join(OUT_DIR, "top30_pares_mas_cercanos.png"))

print("\nPrimeros 20 pares más cercanos:")
print(all_df.head(20).to_string(index=False))
