import os
import re
import csv
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

DATASET_DIR = "20accesos_csv_label"
RESULTS_DIR = "resultados_fingerprints_2d"

os.makedirs(RESULTS_DIR, exist_ok=True)

MAX_LEN = 60


def leer_archivo(path):
    muestras = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line or line.lower().startswith("label"):
                continue

            if "H123-compact" in line or "H123:" in line:
                continue

            if "'h1'" not in line and "'h2'" not in line and "'h3'" not in line:
                continue

            label = line.split(",", 1)[0]

            protocols = re.findall(r"'(h[123])'", line)

            pos_proto = line.find("['h")
            if pos_proto == -1:
                continue

            before_proto = line[:pos_proto]
            listas = re.findall(r"\[[^\[\]]*\]", before_proto)

            if not listas:
                continue

            resources = [int(x) for x in re.findall(r"\d+", listas[-1])]

            if not resources or not protocols:
                continue

            resources = resources[:MAX_LEN]
            protocols = protocols[:MAX_LEN]

            proto_num = []
            for p in protocols:
                if p == "h1":
                    proto_num.append(1)
                elif p == "h2":
                    proto_num.append(2)
                elif p == "h3":
                    proto_num.append(3)
                else:
                    proto_num.append(0)

            resources = resources + [0] * (MAX_LEN - len(resources))
            proto_num = proto_num + [0] * (MAX_LEN - len(proto_num))

            vector = resources + proto_num

            muestras.append((label, vector))

    return muestras


labels = []
vectors = []
files = []

for filename in sorted(os.listdir(DATASET_DIR)):
    if not filename.endswith(".csv"):
        continue

    path = os.path.join(DATASET_DIR, filename)
    muestras = leer_archivo(path)

    for label, vector in muestras:
        labels.append(label)
        vectors.append(vector)
        files.append(filename)

X = np.array(vectors, dtype=float)

print(f"Fingerprints cargados: {len(X)}")
print(f"Labels distintos: {len(set(labels))}")

if len(X) == 0:
    raise SystemExit("No se han cargado fingerprints válidos.")

# Normalización sencilla
X_mean = X.mean(axis=0)
X_std = X.std(axis=0)
X_std[X_std == 0] = 1
X_norm = (X - X_mean) / X_std

# PCA 2D
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_norm)

# Guardar coordenadas
coords_csv = os.path.join(RESULTS_DIR, "fingerprints_2d_pca.csv")

with open(coords_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["archivo", "label", "x", "y"])

    for file, label, point in zip(files, labels, X_2d):
        writer.writerow([file, label, point[0], point[1]])

# Gráfica global
plt.figure(figsize=(28, 22))

unique_labels = sorted(set(labels))

for label in unique_labels:
    idx = [i for i, l in enumerate(labels) if l == label]
    points = X_2d[idx]

    plt.scatter(
        points[:, 0],
        points[:, 1],
        s=18,
        alpha=0.65,
        label=label
    )

plt.xlabel("PCA componente 1")
plt.ylabel("PCA componente 2")
plt.title("Proyección 2D de fingerprints HOLMES/WATSON por sitio web")
plt.grid(alpha=0.3)

# No ponemos leyenda completa porque con 134 labels queda ilegible
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, "fingerprints_2d_todas_webs.png"), dpi=300)
plt.close()

# Gráfica con centroides y etiquetas
plt.figure(figsize=(30, 24))

for label in unique_labels:
    idx = [i for i, l in enumerate(labels) if l == label]
    points = X_2d[idx]

    plt.scatter(points[:, 0], points[:, 1], s=15, alpha=0.45)

    cx = points[:, 0].mean()
    cy = points[:, 1].mean()

    plt.text(cx, cy, label, fontsize=7)

plt.xlabel("PCA componente 1")
plt.ylabel("PCA componente 2")
plt.title("Áreas de fingerprints por sitio web con centroides etiquetados")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, "fingerprints_2d_centroides.png"), dpi=300)
plt.close()

# Calcular dispersión por web
dispersion_rows = []

for label in unique_labels:
    idx = [i for i, l in enumerate(labels) if l == label]
    points = X_2d[idx]

    centroid = points.mean(axis=0)
    distances = np.linalg.norm(points - centroid, axis=1)

    dispersion_rows.append([
        label,
        len(points),
        distances.mean(),
        distances.std(),
        distances.min(),
        distances.max()
    ])

dispersion_csv = os.path.join(RESULTS_DIR, "dispersion_por_web.csv")

with open(dispersion_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "label",
        "num_accesos",
        "dispersion_media",
        "dispersion_desv",
        "dispersion_min",
        "dispersion_max"
    ])
    writer.writerows(dispersion_rows)

print("Resultados generados en:", RESULTS_DIR)
print(" - fingerprints_2d_todas_webs.png")
print(" - fingerprints_2d_centroides.png")
print(" - fingerprints_2d_pca.csv")
print(" - dispersion_por_web.csv")
