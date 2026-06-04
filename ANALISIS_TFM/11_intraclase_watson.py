import os
import sys
import ast
import csv
from itertools import combinations

import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WATSON_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/WATSON"
DISTANCE_DIR = os.path.join(WATSON_DIR, "distance_cal")

sys.path.insert(0, WATSON_DIR)
sys.path.insert(0, DISTANCE_DIR)

import watson_H123_cal_wasserstein
import watson_H123_cal_LCSS


INPUT_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/HOLMES/20accesos_csv_label"

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "estabilidad_intraclase_watson.csv"
)

MAX_LEN = 50
WEIGHT_WASSERSTEIN = 0.5
WEIGHT_LCSS = 0.5
WASSERSTEIN_CONFIG = MAX_LEN
LCSS_CONFIG = 0.1


def parsear_fila_compact(row):
    """
    Espera filas tipo:
    google.com,"([1, 38, 1, ...], ['h1', 'h3', ...])"
    """
    if len(row) < 2:
        return None

    url = row[0].strip()
    contenido = ",".join(row[1:]).strip()

    if "H123-compact" in contenido:
        return None

    if "H123:" in contenido:
        return None

    if not contenido.startswith("("):
        return None

    try:
        seq, httpv = ast.literal_eval(contenido)

        seq = seq[:MAX_LEN]
        httpv = httpv[:MAX_LEN]

        if len(seq) == 0 or len(httpv) == 0:
            return None

        return {
            "url": url,
            "seq": seq,
            "httpv": httpv
        }

    except Exception:
        return None


def cargar_accesos(input_dir):
    accesos = []

    archivos = sorted([
        f for f in os.listdir(input_dir)
        if f.endswith(".csv")
    ])

    print("CSV encontrados:", len(archivos))

    for filename in archivos:
        path = os.path.join(input_dir, filename)

        with open(path, "r", newline="") as f:
            reader = csv.reader(f)

            for row in reader:
                acceso = parsear_fila_compact(row)

                if acceso is not None:
                    acceso["archivo"] = filename
                    accesos.append(acceso)

    df = pd.DataFrame(accesos)

    return df


def calcular_distancias_watson(a1, a2):
    target_num = a1["seq"]
    target_httpv = a1["httpv"]

    controles_num = [a2["seq"]]
    controles_httpv = [a2["httpv"]]

    d_wasserstein = watson_H123_cal_wasserstein.cal_sorted_wasserstein_matrix(
        target_num,
        controles_num,
        target_httpv,
        controles_httpv,
        WASSERSTEIN_CONFIG
    )[0]

    d_lcss = watson_H123_cal_LCSS.batch_greedy_lcs(
        target_num,
        controles_num,
        LCSS_CONFIG
    )[0]

    d_watson = (
        WEIGHT_WASSERSTEIN * d_wasserstein
        + WEIGHT_LCSS * d_lcss
    )

    return d_wasserstein, d_lcss, d_watson


df = cargar_accesos(INPUT_DIR)

if df.empty:
    raise ValueError("No se ha cargado ningún acceso H123-compact válido.")

print("Accesos cargados:", len(df))
print("URLs distintas:", df["url"].nunique())

resultados = []

for url, grupo in df.groupby("url"):
    grupo = grupo.reset_index(drop=True)

    dist_wasserstein = []
    dist_lcss = []
    dist_watson = []

    for i, j in combinations(range(len(grupo)), 2):
        a1 = grupo.iloc[i]
        a2 = grupo.iloc[j]

        try:
            d_wass, d_lcss, d_watson = calcular_distancias_watson(a1, a2)

            dist_wasserstein.append(d_wass)
            dist_lcss.append(d_lcss)
            dist_watson.append(d_watson)

        except Exception:
            continue

    if len(dist_watson) == 0:
        continue

    resultados.append({
        "url": url,
        "num_accesos": len(grupo),

        "media_intra_wasserstein": np.mean(dist_wasserstein),
        "desv_tipica_intra_wasserstein": np.std(dist_wasserstein),
        "min_intra_wasserstein": np.min(dist_wasserstein),
        "max_intra_wasserstein": np.max(dist_wasserstein),

        "media_intra_lcss": np.mean(dist_lcss),
        "desv_tipica_intra_lcss": np.std(dist_lcss),
        "min_intra_lcss": np.min(dist_lcss),
        "max_intra_lcss": np.max(dist_lcss),

        "media_intra_watson": np.mean(dist_watson),
        "desv_tipica_intra_watson": np.std(dist_watson),
        "min_intra_watson": np.min(dist_watson),
        "max_intra_watson": np.max(dist_watson)
    })

res = pd.DataFrame(resultados)

if res.empty:
    raise ValueError("No se ha podido calcular ninguna distancia intra-clase.")

res = res.sort_values(
    "desv_tipica_intra_watson",
    ascending=True
)

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
res.to_csv(OUTPUT_CSV, index=False)

print("\nTOP 20 MÁS ESTABLES SEGÚN WATSON\n")
print(
    res[
        [
            "url",
            "num_accesos",
            "media_intra_watson",
            "desv_tipica_intra_watson",
            "min_intra_watson",
            "max_intra_watson"
        ]
    ].head(20)
)

print("\nTOP 20 MÁS INESTABLES SEGÚN WATSON\n")
print(
    res[
        [
            "url",
            "num_accesos",
            "media_intra_watson",
            "desv_tipica_intra_watson",
            "min_intra_watson",
            "max_intra_watson"
        ]
    ].tail(20)
)

print(f"\nGuardado en {OUTPUT_CSV}")
