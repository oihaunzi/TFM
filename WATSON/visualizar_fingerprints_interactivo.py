import os
import re
import csv
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import plotly.express as px

DATASET_DIR = "20accesos_csv_label"
RESULTS_DIR = "resultados_fingerprints_2d"
OUTPUT_HTML = os.path.join(RESULTS_DIR, "fingerprints_interactivo.html")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "fingerprints_interactivo_pca.csv")

MAX_LEN = 60

os.makedirs(RESULTS_DIR, exist_ok=True)


def leer_archivo(path, filename):
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

            muestras.append({
                "archivo": filename,
                "label": label,
                "access_id": len(muestras) + 1,
                "num_resources_total": sum(resources),
                "num_h1": protocols.count("h1"),
                "num_h2": protocols.count("h2"),
                "num_h3": protocols.count("h3"),
                "vector": vector
            })

    return muestras


rows = []

for filename in sorted(os.listdir(DATASET_DIR)):
    if not filename.endswith(".csv"):
        continue

    path = os.path.join(DATASET_DIR, filename)
    rows.extend(leer_archivo(path, filename))

if not rows:
    raise SystemExit("No se han encontrado fingerprints válidos.")

labels = [r["label"] for r in rows]
vectors = np.array([r["vector"] for r in rows], dtype=float)

print(f"Fingerprints cargados: {len(rows)}")
print(f"Webs distintas: {len(set(labels))}")

# Normalización
mean = vectors.mean(axis=0)
std = vectors.std(axis=0)
std[std == 0] = 1
vectors_norm = (vectors - mean) / std

# PCA
pca = PCA(n_components=2)
coords = pca.fit_transform(vectors_norm)

df = pd.DataFrame({
    "archivo": [r["archivo"] for r in rows],
    "label": [r["label"] for r in rows],
    "access_id": [r["access_id"] for r in rows],
    "x": coords[:, 0],
    "y": coords[:, 1],
    "num_resources_total": [r["num_resources_total"] for r in rows],
    "num_h1": [r["num_h1"] for r in rows],
    "num_h2": [r["num_h2"] for r in rows],
    "num_h3": [r["num_h3"] for r in rows],
})

df.to_csv(OUTPUT_CSV, index=False)

fig = px.scatter(
    df,
    x="x",
    y="y",
    color="label",
    hover_data=[
        "label",
        "archivo",
        "access_id",
        "num_resources_total",
        "num_h1",
        "num_h2",
        "num_h3"
    ],
    title="Proyección interactiva 2D de fingerprints HOLMES/WATSON",
    labels={
        "x": "PCA componente 1",
        "y": "PCA componente 2",
        "label": "Web"
    },
    width=1800,
    height=1100
)

fig.update_traces(
    marker=dict(size=7, opacity=0.75),
    selector=dict(mode="markers")
)

fig.update_layout(
    legend_title_text="Web / label",
    hovermode="closest"
)

fig.write_html(OUTPUT_HTML)

print("Generado:")
print(OUTPUT_HTML)
print(OUTPUT_CSV)
