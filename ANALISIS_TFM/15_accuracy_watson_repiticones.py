import os
import re
import csv
import ast
import subprocess

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting"

WATSON_DIR = os.path.join(ROOT_DIR, "WATSON")
DATASET_H123_DIR = os.path.join(ROOT_DIR, "dataset", "H123")

INPUT_CON_OUTLIERS = os.path.join(ROOT_DIR, "HOLMES", "20accesos_csv_label")
INPUT_SIN_OUTLIERS = os.path.join(ROOT_DIR, "HOLMES", "20accesos_csv_label_sin_outliers")

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_watson_repeticiones.csv"
)

OUTPUT_RESUMEN = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_watson_resumen.csv"
)

REPETICIONES = [20, 50, 100]
DISTANCE = "watson"

WATSON_ORIGINAL = os.path.join(WATSON_DIR, "watson_attack.py")
WATSON_TMP = os.path.join(WATSON_DIR, "watson_attack_tmp_accuracy.py")


def parsear_h123_compact(path):
    accesos = []

    with open(path, "r", newline="") as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 2:
                continue

            label = row[0].strip()
            contenido = ",".join(row[1:]).strip()

            if label == "label":
                continue

            if "H123-compact:" in contenido:
                continue

            if "H123:" in contenido:
                continue

            if not contenido.startswith("("):
                continue

            try:
                seq, protocols = ast.literal_eval(contenido)

                seq = [int(x) for x in seq]
                protocols = [str(p) for p in protocols]

                if len(seq) == 0 or len(protocols) == 0:
                    continue

                accesos.append((label, seq, protocols))

            except Exception:
                continue

    return accesos


def limpiar_dataset():
    os.makedirs(DATASET_H123_DIR, exist_ok=True)

    for f in os.listdir(DATASET_H123_DIR):
        if f.endswith(".csv"):
            os.remove(os.path.join(DATASET_H123_DIR, f))


def preparar_dataset_por_acceso(input_dir):
    """
    Convierte:
        un archivo por URL con varios accesos

    en:
        result_1.csv con el acceso 1 de todas las URLs
        result_2.csv con el acceso 2 de todas las URLs
        ...
    """

    limpiar_dataset()

    por_url = {}

    archivos = sorted([
        f for f in os.listdir(input_dir)
        if f.endswith(".csv")
    ])

    for archivo in archivos:
        path = os.path.join(input_dir, archivo)
        accesos = parsear_h123_compact(path)

        if not accesos:
            continue

        url = accesos[0][0]
        por_url[url] = accesos

    if not por_url:
        raise ValueError("No se han encontrado accesos H123-compact válidos.")

    min_accesos = min(len(v) for v in por_url.values())

    if min_accesos < 2:
        raise ValueError("No hay suficientes accesos por URL para ejecutar WATSON.")

    num_result_files = min(min_accesos, 40)

    for i in range(num_result_files):
        output_file = os.path.join(DATASET_H123_DIR, f"result_{i + 1}.csv")

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)

            for url, accesos in por_url.items():
                label, seq, protocols = accesos[i]
                writer.writerow([label, repr(seq), repr(protocols)])

    print(f"Dataset preparado desde: {input_dir}")
    print(f"URLs cargadas: {len(por_url)}")
    print(f"Accesos por URL usados: {num_result_files}")
    print(f"Archivos result_i.csv creados: {num_result_files}")

    return num_result_files


def crear_watson_temporal(num_result_files):
    with open(WATSON_ORIGINAL, "r") as f:
        codigo = f.read()

    # Ajustar número de result_i.csv disponibles.
    codigo = re.sub(
        r"file_list\s*=\s*\['result_'\s*\+\s*str\(i\)\s*\+\s*'\.csv'\s*for\s*i\s*in\s*range\(1,\s*41\)\]",
        f"file_list = ['result_' + str(i) + '.csv' for i in range(1, {num_result_files + 1})]",
        codigo
    )

    # Evitar fallo cuando el filtro por suma deja wfp_controls vacío.
    codigo = codigo.replace(
"""        match config[3]:""",
"""        if len(wfp_controls) == 0:
            wfp_controls = wfp_ref
            httpv_controls = httpv_ref
            flag_controls = wfp_key_ref

        match config[3]:"""
    )

    with open(WATSON_TMP, "w") as f:
        f.write(codigo)


def ejecutar_watson(N):
    cmd = [
        "python3",
        os.path.basename(WATSON_TMP),
        "--N",
        str(N),
        "--distance",
        DISTANCE
    ]

    proc = subprocess.run(
        cmd,
        cwd=WATSON_DIR,
        capture_output=True,
        text=True
    )

    salida = proc.stdout + proc.stderr

    match = re.search(r"WF ACC:\s*([0-9.]+)", salida)

    if not match:
        print("\nSALIDA COMPLETA DE WATSON:\n")
        print(salida)
        raise ValueError("No se pudo encontrar WF ACC en la salida de WATSON.")

    return float(match.group(1))


resultados = []

experimentos = [
    ("con_outliers", INPUT_CON_OUTLIERS),
    ("sin_outliers", INPUT_SIN_OUTLIERS)
]

for nombre_dataset, ruta_dataset in experimentos:
    num_result_files = preparar_dataset_por_acceso(ruta_dataset)
    crear_watson_temporal(num_result_files)

    N = num_result_files - 1

    for num_repeticiones in REPETICIONES:
        print(f"\nEjecutando {num_repeticiones} repeticiones - {nombre_dataset}\n")

        for rep in range(1, num_repeticiones + 1):
            acc = ejecutar_watson(N)

            resultados.append({
                "dataset": nombre_dataset,
                "repeticiones_configuradas": num_repeticiones,
                "repeticion": rep,
                "N": N,
                "distance": DISTANCE,
                "accuracy": acc
            })

            print(
                f"{nombre_dataset} | "
                f"bloque {num_repeticiones} | "
                f"rep {rep}/{num_repeticiones} | "
                f"acc = {acc:.4f}"
            )


df = pd.DataFrame(resultados)

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

df.to_csv(OUTPUT_CSV, index=False)

resumen = df.groupby(
    ["dataset", "repeticiones_configuradas"]
)["accuracy"].agg(
    media_accuracy="mean",
    desv_tipica_accuracy="std",
    min_accuracy="min",
    max_accuracy="max",
    mediana_accuracy="median"
).reset_index()

resumen.to_csv(OUTPUT_RESUMEN, index=False)

print("\nRESUMEN FINAL\n")
print(resumen)

print(f"\nResultados completos guardados en: {OUTPUT_CSV}")
print(f"Resumen guardado en: {OUTPUT_RESUMEN}")
