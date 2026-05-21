import os
import re
import csv
import yaml
import math
import random
import statistics
import numpy as np

from distance_cal import (
    watson_H123_cal_wasserstein,
    watson_H123_cal_LCSS,
)

DATASET_DIR = "20accesos_csv_label"
OUTPUT_FILE = "resultados_watson_intra_csv.csv"

TOTAL_RUNS = 20
DISTANCE = "watson"


def leer_archivo(path, L):
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

            resources = resources[:L]
            protocols = protocols[:L]

            if resources and protocols:
                muestras.append({
                    "label": label,
                    "resources": resources,
                    "protocols": protocols,
                    "access_id": len(muestras) + 1,
                })

    return muestras


def calcular_watson(test_sample, ref_samples, config):
    L, W, T, distance = config

    target_num = test_sample["resources"]
    target_http = test_sample["protocols"]

    down_filter = sum(target_num) - math.ceil(sum(target_num) * 0.2)
    up_filter = sum(target_num) + math.ceil(sum(target_num) * 0.2)

    wfp_controls = []
    httpv_controls = []

    for ref in ref_samples:
        if down_filter <= sum(ref["resources"]) <= up_filter:
            wfp_controls.append(ref["resources"])
            httpv_controls.append(ref["protocols"])

    if not wfp_controls:
        return None

    weight_wasserstein = W
    weight_lcss = 1 - W

    scores = (
        weight_lcss * watson_H123_cal_LCSS.batch_greedy_lcs(
            target_num,
            wfp_controls,
            T
        )
        + weight_wasserstein * watson_H123_cal_wasserstein.cal_sorted_wasserstein_matrix(
            target_num,
            wfp_controls,
            target_http,
            httpv_controls,
            L
        )
    )

    if len(scores) == 0:
        return None

    scores_array = np.array(scores, dtype=float)

    # Esto es el valor WATSON que usa el algoritmo para elegir la muestra más cercana
    watson_distance = float(scores_array[np.argmin(scores_array)])

    return watson_distance


def ejecutar_archivo(filename, config):
    path = os.path.join(DATASET_DIR, filename)
    muestras = leer_archivo(path, config[0])

    if len(muestras) < 2:
        print(f"[AVISO] {filename} no tiene suficientes accesos válidos")
        return None

    label = muestras[0]["label"]

    watson_values = []
    access_ids = []

    for run in range(1, TOTAL_RUNS + 1):
        test_sample = random.choice(muestras)

        ref_samples = [
            m for m in muestras
            if m is not test_sample
        ]

        watson_value = calcular_watson(
            test_sample,
            ref_samples,
            config
        )

        access_ids.append(test_sample["access_id"])

        if watson_value is not None:
            watson_values.append(watson_value)
            print(
                f"{filename} run={run} "
                f"access={test_sample['access_id']} "
                f"watson={watson_value}"
            )
        else:
            watson_values.append("")
            print(
                f"{filename} run={run} "
                f"access={test_sample['access_id']} "
                f"watson=sin_resultado"
            )

    valores_numericos = [
        x for x in watson_values
        if isinstance(x, float)
    ]

    return {
        "archivo": filename,
        "label": label,
        "num_accesos": len(muestras),

        "watson_run_1": watson_values[0],
        "watson_run_5": watson_values[4],
        "watson_run_10": watson_values[9],
        "watson_run_20": watson_values[19],

        "accesos_test_20_runs": ";".join(str(x) for x in access_ids),
        "watson_20_runs": ";".join(str(x) for x in watson_values),

        "watson_media_20": statistics.mean(valores_numericos) if valores_numericos else "",
        "watson_desv_20": statistics.stdev(valores_numericos) if len(valores_numericos) > 1 else "",
    }


def main():
    with open("../config.yaml", "r") as configfile:
        config_yaml = yaml.safe_load(configfile)

    L = config_yaml["H123_fingerprint"]["max_len"]
    W = config_yaml["H123_fingerprint"]["distance_measurement_weight"]
    T = config_yaml["H123_fingerprint"]["LCSS_sim_threshold"]

    config = [L, W, T, DISTANCE]

    files = sorted([
        f for f in os.listdir(DATASET_DIR)
        if f.endswith(".csv")
    ])

    rows = []

    for filename in files:
        row = ejecutar_archivo(filename, config)

        if row is not None:
            rows.append(row)

    fieldnames = [
        "archivo",
        "label",
        "num_accesos",

        "watson_run_1",
        "watson_run_5",
        "watson_run_10",
        "watson_run_20",

        "accesos_test_20_runs",
        "watson_20_runs",

        "watson_media_20",
        "watson_desv_20",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResultados guardados en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
