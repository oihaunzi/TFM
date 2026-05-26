import os
import glob
import re
import ast
import random
import numpy as np
import pandas as pd


DATA_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/WATSON/20accesos_csv_label"
OUT_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/WATSON/resultados_intra_clase"

N_ITERACIONES = 100
RANDOM_SEED = 42

os.makedirs(OUT_DIR, exist_ok=True)
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ============================================================
# DISTANCIAS TIPO WATSON
# ============================================================

def wasserstein_1d(a, b):
    """
    Wasserstein 1D simplificada.
    Compara dos secuencias numéricas.
    """
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
    """
    Distancia LCSS normalizada.
    0 = idéntico
    1 = totalmente distinto
    """
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


def normalizar_wasserstein(d, max_val):
    if max_val == 0:
        return 0.0
    return d / max_val


def watson_distance(fp1, fp2, max_wass):
    """
    Distancia combinada tipo WATSON:
    50% Wasserstein + 50% LCSS.

    Si en tu watson_attack.py el peso es distinto,
    cambia PESO_WASS y PESO_LCSS.
    """
    PESO_WASS = 0.5
    PESO_LCSS = 0.5

    valores1 = fp1["valores"]
    valores2 = fp2["valores"]

    proto1 = fp1["protocolos"]
    proto2 = fp2["protocolos"]

    d_wass_raw = wasserstein_1d(valores1, valores2)
    d_wass = normalizar_wasserstein(d_wass_raw, max_wass)

    d_lcss = lcss_distance(proto1, proto2)

    d_total = PESO_WASS * d_wass + PESO_LCSS * d_lcss

    return d_total, d_wass, d_lcss


# ============================================================
# LECTURA DE H123-COMPACT
# ============================================================

def parse_h123_compact(linea):
    """
    Extrae:
    - URL
    - lista de valores
    - lista de protocolos h1/h2/h3

    Está hecho robusto porque algunos CSV tienen formato irregular.
    """
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
            "H1": protocolos.count("h1"),
            "H2": protocolos.count("h2"),
            "H3": protocolos.count("h3")
        }

    except Exception:
        return None


def cargar_fingerprints():
    fingerprints = []

    archivos = sorted(
        glob.glob(os.path.join(DATA_DIR, "**/*"), recursive=True)
    )
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
                        fingerprints.append(fp)
                        acceso += 1

    return pd.DataFrame(fingerprints)


# ============================================================
# ANÁLISIS INTRA-CLASE
# ============================================================

def main():
    df = cargar_fingerprints()

    if df.empty:
        print("No se han encontrado fingerprints H123-compact.")
        return

    print(f"Fingerprints cargados: {len(df)}")
    print(f"URLs distintas: {df['url'].nunique()}")

    max_val_global = 0

    for valores in df["valores"]:
        if len(valores) > 0:
            max_val_global = max(max_val_global, max(valores))

    print(f"Máximo global para normalizar Wasserstein: {max_val_global}")

    detalle = []
    resumen = []

    for url, grupo in df.groupby("url"):
        grupo = grupo.reset_index(drop=True)

        if len(grupo) < 2:
            continue

        distancias_iteracion = []
        accesos_usados = []

        for it in range(1, N_ITERACIONES + 1):
            idx_ref = random.randint(0, len(grupo) - 1)
            ref = grupo.iloc[idx_ref]

            distancias = []
            dist_wass = []
            dist_lcss = []

            for idx_cmp in range(len(grupo)):
                if idx_cmp == idx_ref:
                    continue

                cmp_fp = grupo.iloc[idx_cmp]

                d_total, d_w, d_l = watson_distance(
                    ref,
                    cmp_fp,
                    max_val_global
                )

                distancias.append(d_total)
                dist_wass.append(d_w)
                dist_lcss.append(d_l)

            media = float(np.mean(distancias))
            desviacion = float(np.std(distancias))
            minimo = float(np.min(distancias))
            maximo = float(np.max(distancias))

            distancias_iteracion.extend(distancias)
            accesos_usados.append(int(ref["acceso"]))

            detalle.append({
                "url": url,
                "iteracion": it,
                "acceso_referencia": int(ref["acceso"]),
                "captura_referencia": ref["archivo"],
                "H1_ref": int(ref["H1"]),
                "H2_ref": int(ref["H2"]),
                "H3_ref": int(ref["H3"]),
                "distancia_media": media,
                "distancia_desviacion": desviacion,
                "distancia_minima": minimo,
                "distancia_maxima": maximo,
                "wasserstein_media": float(np.mean(dist_wass)),
                "lcss_media": float(np.mean(dist_lcss))
            })

        accesos_unicos = sorted(set(accesos_usados))
        conteo_accesos = {
            acc: accesos_usados.count(acc)
            for acc in accesos_unicos
        }

        resumen.append({
            "url": url,
            "num_accesos": len(grupo),
            "iteraciones": N_ITERACIONES,
            "media_intra_clase": float(np.mean(distancias_iteracion)),
            "desviacion_intra_clase": float(np.std(distancias_iteracion)),
            "min_intra_clase": float(np.min(distancias_iteracion)),
            "max_intra_clase": float(np.max(distancias_iteracion)),
            "accesos_usados": ",".join(map(str, accesos_unicos)),
            "conteo_accesos_usados": str(conteo_accesos)
        })

    df_detalle = pd.DataFrame(detalle)
    df_resumen = pd.DataFrame(resumen)

    salida_detalle_csv = os.path.join(
        OUT_DIR,
        "tabla_detalle_intra_clase_watson.csv"
    )

    salida_resumen_csv = os.path.join(
        OUT_DIR,
        "tabla_resumen_intra_clase_watson.csv"
    )

    salida_excel = os.path.join(
        OUT_DIR,
        "resultados_intra_clase_watson.xlsx"
    )

    df_detalle.to_csv(salida_detalle_csv, index=False)
    df_resumen.to_csv(salida_resumen_csv, index=False)

    with pd.ExcelWriter(salida_excel) as writer:
        df_resumen.to_excel(writer, sheet_name="resumen_por_url", index=False)
        df_detalle.to_excel(writer, sheet_name="detalle_iteraciones", index=False)

    print("\nGenerado:")
    print(salida_resumen_csv)
    print(salida_detalle_csv)
    print(salida_excel)

    print("\nPrimeras filas resumen:")
    print(df_resumen.head())


if __name__ == "__main__":
    main()
