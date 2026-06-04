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

INPUT_INTRA = os.path.join(
    BASE_DIR,
    "resultados",
    "estabilidad_intraclase_watson.csv"
)

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "interclase_watson_solapes.csv"
)

MAX_LEN = 50
WEIGHT_WASSERSTEIN = 0.5
WEIGHT_LCSS = 0.5
WASSERSTEIN_CONFIG = MAX_LEN
LCSS_CONFIG = 0.1
TOL = 1e-12


def parsear_fila_compact(row):
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

            contador_fila = 0

            for row in reader:
                contador_fila += 1
                acceso = parsear_fila_compact(row)

                if acceso is not None:
                    acceso["archivo"] = filename
                    acceso["linea"] = contador_fila
                    accesos.append(acceso)

    df = pd.DataFrame(accesos)

    df["access_id"] = (
        df["archivo"].astype(str)
        + ":linea_"
        + df["linea"].astype(str)
    )

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

intra = pd.read_csv(INPUT_INTRA)

if "max_intra_watson" not in intra.columns:
    raise ValueError("La tabla intra debe tener la columna max_intra_watson.")

max_intra_por_url = dict(zip(intra["url"], intra["max_intra_watson"]))

urls = sorted(df["url"].unique())

mejores = {}

for url in urls:
    mejores[url] = {
        "url": url,
        "max_intra": max_intra_por_url.get(url, np.nan),
        "min_inter": np.inf,
        "url_mas_cercana": None,
        "access_id_url": None,
        "access_id_url_mas_cercana": None,
        "distancia_wasserstein_min": np.nan,
        "distancia_lcss_min": np.nan,
        "distancia_watson_min": np.nan
    }


for url_1, url_2 in combinations(urls, 2):
    grupo_1 = df[df["url"] == url_1].reset_index(drop=True)
    grupo_2 = df[df["url"] == url_2].reset_index(drop=True)

    for _, a1 in grupo_1.iterrows():
        for _, a2 in grupo_2.iterrows():
            try:
                d_wass, d_lcss, d_watson = calcular_distancias_watson(a1, a2)

                if d_watson < mejores[url_1]["min_inter"]:
                    mejores[url_1]["min_inter"] = d_watson
                    mejores[url_1]["url_mas_cercana"] = url_2
                    mejores[url_1]["access_id_url"] = a1["access_id"]
                    mejores[url_1]["access_id_url_mas_cercana"] = a2["access_id"]
                    mejores[url_1]["distancia_wasserstein_min"] = d_wass
                    mejores[url_1]["distancia_lcss_min"] = d_lcss
                    mejores[url_1]["distancia_watson_min"] = d_watson

                if d_watson < mejores[url_2]["min_inter"]:
                    mejores[url_2]["min_inter"] = d_watson
                    mejores[url_2]["url_mas_cercana"] = url_1
                    mejores[url_2]["access_id_url"] = a2["access_id"]
                    mejores[url_2]["access_id_url_mas_cercana"] = a1["access_id"]
                    mejores[url_2]["distancia_wasserstein_min"] = d_wass
                    mejores[url_2]["distancia_lcss_min"] = d_lcss
                    mejores[url_2]["distancia_watson_min"] = d_watson

            except Exception:
                continue


resultados = []

for url in urls:
    fila = mejores[url]

    max_intra = fila["max_intra"]
    min_inter = fila["min_inter"]

    if np.isinf(min_inter):
        continue

    riesgo_solape = bool(max_intra >= min_inter)
    solape_exacto = bool(abs(max_intra - min_inter) <= TOL)

    resultados.append({
        "url": url,
        "max_intra": max_intra,
        "min_inter": min_inter,
        "url_mas_cercana": fila["url_mas_cercana"],
        "access_id_url": fila["access_id_url"],
        "access_id_url_mas_cercana": fila["access_id_url_mas_cercana"],
        "riesgo_solape": riesgo_solape,
        "solape_exacto": solape_exacto,
        "distancia_wasserstein_min": fila["distancia_wasserstein_min"],
        "distancia_lcss_min": fila["distancia_lcss_min"],
        "distancia_watson_min": fila["distancia_watson_min"]
    })

res = pd.DataFrame(resultados)

res = res.sort_values(
    ["riesgo_solape", "min_inter"],
    ascending=[False, True]
)

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
res.to_csv(OUTPUT_CSV, index=False)

print("\nTOP 20 URLs CON MAYOR RIESGO DE SOLAPE SEGÚN WATSON\n")
print(
    res[
        [
            "url",
            "max_intra",
            "min_inter",
            "url_mas_cercana",
            "access_id_url",
            "access_id_url_mas_cercana",
            "riesgo_solape",
            "solape_exacto"
        ]
    ].head(20)
)

print(f"\nGuardado en {OUTPUT_CSV}")
