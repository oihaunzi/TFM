import os
import numpy as np
import pandas as pd
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "puntos_3d_H123_sin_outliers.csv"
)

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "estabilidad_intraclase_sin_outliers.csv"
)

df = pd.read_csv(INPUT_CSV)
df.columns = df.columns.str.strip()

resultados = []

for url, grupo in df.groupby("url"):

    puntos = grupo[["H1", "H2", "H3"]].values

    distancias = []

    for p1, p2 in combinations(puntos, 2):
        d = np.linalg.norm(p1 - p2)
        distancias.append(d)

    if len(distancias) == 0:
        resultados.append({
            "url": url,
            "num_accesos": len(grupo),
            "media_intra": 0,
            "desv_tipica_intra": 0,
            "min_intra": 0,
            "max_intra": 0
        })
        continue

    resultados.append({
        "url": url,
        "num_accesos": len(grupo),
        "media_intra": np.mean(distancias),
        "desv_tipica_intra": np.std(distancias),
        "min_intra": np.min(distancias),
        "max_intra": np.max(distancias)
    })

res = pd.DataFrame(resultados)

res = res.sort_values(
    "desv_tipica_intra",
    ascending=True
)

res.to_csv(OUTPUT_CSV, index=False)

print("\nTOP 20 MÁS ESTABLES SIN OUTLIERS\n")
print(
    res[
        ["url", "num_accesos", "media_intra", "desv_tipica_intra", "min_intra", "max_intra"]
    ].head(20)
)

print("\nTOP 20 MÁS INESTABLES SIN OUTLIERS\n")
print(
    res[
        ["url", "num_accesos", "media_intra", "desv_tipica_intra", "min_intra", "max_intra"]
    ].tail(20)
)

print(f"\n[OK] Guardado en: {OUTPUT_CSV}")
