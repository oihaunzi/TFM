import os
import glob
import re
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "..", "HOLMES", "20accesos_csv_label")
OUTPUT_DIR = os.path.join(BASE_DIR, "resultados")

OUTPUT_CSV = os.path.join(OUTPUT_DIR, "puntos_3d_H123.csv")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "mapa_3d_H123_filtrable.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extraer_listas_h123(linea):
    """
    Extrae las tres listas numéricas de una línea H123 real:
    gmail.com,[[1,"0, 0, 0, 0, 0, 0], [0, 0, 1, 1, 1, 2, 6], [0, 2, 0, 0, 0, 0, 0]]"
    """

    if "," not in linea:
        return None

    _, contenido = linea.split(",", 1)

    contenido = contenido.replace('"', "")

    listas = re.findall(r"\[([0-9,\s]+)\]", contenido)

    if len(listas) < 3:
        return None

    h1 = [int(x) for x in re.findall(r"\d+", listas[0])]
    h2 = [int(x) for x in re.findall(r"\d+", listas[1])]
    h3 = [int(x) for x in re.findall(r"\d+", listas[2])]

    return h1, h2, h3

def procesar_csv_h123(file_path):
    puntos = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lineas = [line.strip() for line in f if line.strip()]

    access_id = 1

    for i in range(len(lineas) - 1):
        if ",H123:" not in lineas[i]:
            continue

        linea_datos = lineas[i + 1]
        url = linea_datos.split(",", 1)[0].strip()

        listas = extraer_listas_h123(linea_datos)

        if listas is None:
            print(f"[AVISO] No se pudo extraer H123 en {os.path.basename(file_path)} línea {i+2}")
            continue

        h1_lista, h2_lista, h3_lista = listas

        puntos.append({
            "url": url,
            "archivo": os.path.basename(file_path),
            "access_id": access_id,
            "H1": sum(h1_lista),
            "H2": sum(h2_lista),
            "H3": sum(h3_lista),
            "H1_lista": str(h1_lista),
            "H2_lista": str(h2_lista),
            "H3_lista": str(h3_lista)
        })

        access_id += 1

    return puntos


csv_files = sorted(glob.glob(os.path.join(INPUT_DIR, "**", "*.csv"), recursive=True))

if not csv_files:
    raise FileNotFoundError(f"No se han encontrado CSV en: {INPUT_DIR}")

print(f"[INFO] CSV encontrados: {len(csv_files)}")

todos = []

for file_path in csv_files:
    puntos_archivo = procesar_csv_h123(file_path)
    todos.extend(puntos_archivo)

if not todos:
    raise RuntimeError("No se ha extraído ningún punto H123.")

df = pd.DataFrame(todos)

df.to_csv(OUTPUT_CSV, index=False)

print(f"[OK] CSV creado: {OUTPUT_CSV}")
print(f"[INFO] Total puntos: {len(df)}")
print(f"[INFO] Total URLs: {df['url'].nunique()}")

print("\n[INFO] Accesos por URL:")
print(df.groupby("url").size().sort_values())


fig = px.scatter_3d(
    df,
    x="H1",
    y="H2",
    z="H3",
    color="url",
    hover_data=["url", "archivo", "access_id", "H1", "H2", "H3"],
    title="Mapa 3D de firmas H1-H2-H3 por URL",
    labels={
        "H1": "Dimensión 1: número de recursos H1",
        "H2": "Dimensión 2: número de recursos H2",
        "H3": "Dimensión 3: número de recursos H3",
        "url": "URL"
    }
)

fig.update_traces(marker=dict(size=5, opacity=0.75))

fig.update_layout(
    legend_title_text="URL",
    scene=dict(
        xaxis_title="H1",
        yaxis_title="H2",
        zaxis_title="H2"
    )
)

fig.write_html(OUTPUT_HTML)

print(f"[OK] Mapa 3D generado: {OUTPUT_HTML}")
