import os
import glob
import re
from itertools import combinations

import numpy as np
import pandas as pd


BASE_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/WATSON"

DATA_DIR = os.path.join(BASE_DIR, "20accesos_csv_label")

INTRA_CSV = os.path.join(
    BASE_DIR,
    "resultados_intra_clase",
    "tabla_resumen_intra_clase_watson.csv"
)

OUT_DIR = os.path.join(BASE_DIR, "resultados_inter_clase_por_origen")
os.makedirs(OUT_DIR, exist_ok=True)


def wasserstein_1d(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)

    if len(a) == 0 or len(b) == 0:
        return 1.0

    a = np.sort(a)
    b = np.sort(b)

    n = max(len(a), len(b))

    qa = np.interp(
        np.linspace(0, 1, n),
        np.linspace(0, 1, len(a)),
        a
    )

    qb = np.interp(
        np.linspace(0, 1, n),
        np.linspace(0, 1, len(b)),
        b
    )

    return float(np.mean(np.abs(qa - qb)))


def lcss_distance(seq1, seq2):
    n = len(seq1)
    m = len(seq2)

    if n == 0 or m == 0:
        return 1.0

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n):
        for j in range(m):
            if seq1[i] == seq2[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(
                    dp[i][j + 1],
                    dp[i + 1][j]
                )

    lcss = dp[n][m]
    return 1.0 - (lcss / min(n, m))


def watson_distance(fp1, fp2, max_val_global):
    peso_wasserstein = 0.5
    peso_lcss = 0.5

    d_w_raw = wasserstein_1d(fp1["valores"], fp2["valores"])

    if max_val_global == 0:
        d_w = 0.0
    else:
        d_w = d_w_raw / max_val_global

    d_lcss = lcss_distance(fp1["protocolos"], fp2["protocolos"])

    return peso_wasserstein * d_w + peso_lcss * d_lcss


def parse_h123_compact(linea):
    try:
        url, contenido = linea.split(",", 1)
        url = url.strip()

        protocolos = re.findall(r"'h[123]'", contenido)
        protocolos = [p.replace("'", "") for p in protocolos]

        numeros_txt = re.findall(r"\d+", contenido.split("]")[0])
        valores = [int(x) for x in numeros_txt]

        if len(protocolos) == 0:
            return None

        return {
            "url": url,
            "valores": valores,
            "protocolos": protocolos,
        }

    except Exception:
        return None


def cargar_fingerprints():
    datos = []

    archivos = sorted(glob.glob(os.path.join(DATA_DIR, "**/*"), recursive=True))
    archivos = [a for a in archivos if os.path.isfile(a)]

    print(f"Archivos encontrados: {len(archivos)}")

    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()

        acceso = 1

        for i, linea in enumerate(lineas):
            if "H123-compact:" in linea:
                if i + 1 < len(lineas):
                    fp = parse_h123_compact(lineas[i + 1].strip())

                    if fp is not None:
                        fp["archivo"] = os.path.basename(archivo)
                        fp["acceso"] = acceso
                        datos.append(fp)
                        acceso += 1

    return pd.DataFrame(datos)


def main():
    print("Cargando fingerprints...")
    df_fp = cargar_fingerprints()

    if df_fp.empty:
        print("No se han encontrado fingerprints.")
        return

    print(f"Fingerprints cargados: {len(df_fp)}")
    print(f"URLs distintas: {df_fp['url'].nunique()}")

    print("Cargando tabla intra-clase...")
    df_intra = pd.read_csv(INTRA_CSV)

    intra_info = {}

    for _, row in df_intra.iterrows():
        intra_info[row["url"]] = {
            "max_intra": float(row["max_intra_clase"]),
            "media_intra": float(row["media_intra_clase"]),
            "desviacion_intra": float(row["desviacion_intra_clase"]),
        }

    max_val_global = 0

    for valores in df_fp["valores"]:
        if len(valores) > 0:
            max_val_global = max(max_val_global, max(valores))

    print(f"Máximo global para normalizar Wasserstein: {max_val_global}")

    urls = sorted(df_fp["url"].unique())

    pares_dirigidos = []

    resumen = {
        url: {
            "url": url,
            "max_intra": intra_info[url]["max_intra"],
            "media_intra": intra_info[url]["media_intra"],
            "desviacion_intra": intra_info[url]["desviacion_intra"],
            "min_inter": None,
            "url_mas_cerca": None,
            "riesgo_solape": "No",
            "num_urls_solapadas": 0
        }
        for url in urls
        if url in intra_info
    }

    print("Calculando distancias inter-clase por URL origen...")

    for url_a, url_b in combinations(urls, 2):
        if url_a not in intra_info or url_b not in intra_info:
            continue

        grupo_a = df_fp[df_fp["url"] == url_a].to_dict("records")
        grupo_b = df_fp[df_fp["url"] == url_b].to_dict("records")

        distancias = []

        for fp_a in grupo_a:
            for fp_b in grupo_b:
                d = watson_distance(fp_a, fp_b, max_val_global)
                distancias.append(d)

        min_inter = float(np.min(distancias))

        # Evaluación desde A hacia B
        max_intra_a = intra_info[url_a]["max_intra"]
        solape_a = "Sí" if min_inter <= max_intra_a else "No"

        pares_dirigidos.append({
            "url_origen": url_a,
            "url_comparada": url_b,
            "max_intra_origen": max_intra_a,
            "min_inter": min_inter,
            "solape": solape_a
        })

        if resumen[url_a]["min_inter"] is None or min_inter < resumen[url_a]["min_inter"]:
            resumen[url_a]["min_inter"] = min_inter
            resumen[url_a]["url_mas_cerca"] = url_b

        if solape_a == "Sí":
            resumen[url_a]["riesgo_solape"] = "Sí"
            resumen[url_a]["num_urls_solapadas"] += 1

        # Evaluación desde B hacia A
        max_intra_b = intra_info[url_b]["max_intra"]
        solape_b = "Sí" if min_inter <= max_intra_b else "No"

        pares_dirigidos.append({
            "url_origen": url_b,
            "url_comparada": url_a,
            "max_intra_origen": max_intra_b,
            "min_inter": min_inter,
            "solape": solape_b
        })

        if resumen[url_b]["min_inter"] is None or min_inter < resumen[url_b]["min_inter"]:
            resumen[url_b]["min_inter"] = min_inter
            resumen[url_b]["url_mas_cerca"] = url_a

        if solape_b == "Sí":
            resumen[url_b]["riesgo_solape"] = "Sí"
            resumen[url_b]["num_urls_solapadas"] += 1

    df_pares = pd.DataFrame(pares_dirigidos)
    df_resumen = pd.DataFrame(list(resumen.values()))

    df_resumen = df_resumen.sort_values(
        by=["riesgo_solape", "num_urls_solapadas", "min_inter"],
        ascending=[False, False, True]
    )

    df_pares = df_pares.sort_values(
        by=["solape", "url_origen", "min_inter"],
        ascending=[False, True, True]
    )

    salida_resumen = os.path.join(
        OUT_DIR,
        "tabla_1_resumen_solape_por_url.csv"
    )

    salida_pares = os.path.join(
        OUT_DIR,
        "tabla_2_solapes_por_origen.csv"
    )

    salida_solo_solapes = os.path.join(
        OUT_DIR,
        "tabla_2_solo_solapes_por_origen.csv"
    )

    df_resumen.to_csv(salida_resumen, index=False)
    df_pares.to_csv(salida_pares, index=False)
    df_pares[df_pares["solape"] == "Sí"].to_csv(
        salida_solo_solapes,
        index=False
    )

    print("\nResultados generados:")
    print(salida_resumen)
    print(salida_pares)
    print(salida_solo_solapes)

    print("\nResumen:")
    print(f"URLs analizadas: {len(df_resumen)}")
    print(f"Comparaciones dirigidas: {len(df_pares)}")
    print(f"Solapes detectados: {(df_pares['solape'] == 'Sí').sum()}")


if __name__ == "__main__":
    main()
