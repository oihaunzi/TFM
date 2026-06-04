import os
import numpy as np
import pandas as pd
from itertools import combinations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(BASE_DIR, "resultados", "puntos_3d_H123.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "resultados", "inter_solapes_con_outliers.csv")


def distancia(p1, p2):
    return np.linalg.norm(p1 - p2)


df = pd.read_csv(INPUT_CSV)
df.columns = df.columns.str.strip()

resultados = []

urls = sorted(df["url"].unique())

# Precalcular max_intra por URL
max_intra_por_url = {}

for url in urls:
    grupo = df[df["url"] == url]
    puntos = grupo[["H1", "H2", "H3"]].values

    distancias_intra = []

    for p1, p2 in combinations(puntos, 2):
        distancias_intra.append(distancia(p1, p2))

    if len(distancias_intra) == 0:
        max_intra_por_url[url] = 0
    else:
        max_intra_por_url[url] = max(distancias_intra)


# Comparar cada URL contra el resto
for url_a in urls:
    grupo_a = df[df["url"] == url_a]
    puntos_a = grupo_a[["H1", "H2", "H3"]].values

    mejor_url_b = None
    min_inter_global = float("inf")
    punto_a_min = None
    punto_b_min = None
    solape_exacto = "No"

    for url_b in urls:
        if url_a == url_b:
            continue

        grupo_b = df[df["url"] == url_b]
        puntos_b = grupo_b[["H1", "H2", "H3"]].values

        for idx_a, p_a in enumerate(puntos_a):
            for idx_b, p_b in enumerate(puntos_b):

                d = distancia(p_a, p_b)

                if d < min_inter_global:
                    min_inter_global = d
                    mejor_url_b = url_b
                    punto_a_min = grupo_a.iloc[idx_a]["access_id"]
                    punto_b_min = grupo_b.iloc[idx_b]["access_id"]

                if d == 0:
                    solape_exacto = "Sí"

    max_intra = max_intra_por_url[url_a]

    riesgo_solape = "Sí" if max_intra > min_inter_global else "No"

    resultados.append({
        "url": url_a,
        "max_intra": max_intra,
        "min_inter": min_inter_global,
        "url_mas_cercana": mejor_url_b,
        "access_id_url": punto_a_min,
        "access_id_url_mas_cercana": punto_b_min,
        "riesgo_solape": riesgo_solape,
        "solape_exacto": solape_exacto
    })

res = pd.DataFrame(resultados)

res = res.sort_values(
    by=["riesgo_solape", "min_inter"],
    ascending=[False, True]
)

res.to_csv(OUTPUT_CSV, index=False)

print("\nTABLA INTER-CLASE CON OUTLIERS\n")
print(res.head(30))

print(f"\n[OK] Guardado en: {OUTPUT_CSV}")

print("\nResumen:")
print(res["riesgo_solape"].value_counts())
print(res["solape_exacto"].value_counts())
