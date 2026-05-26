import os
import glob
import re
import pandas as pd
import plotly.express as px
import numpy as np

CARPETA = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/graficas/20accesos_csv_label"
SALIDA_HTML = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/graficas/holmes_3d_interactivo_grande.html"
SALIDA_CSV = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/graficas/holmes_3d_puntos.csv"

datos = []


def procesar_linea_compact(linea):
    try:
        url, contenido = linea.split(",", 1)

        protocolos = re.findall(r"'h[123]'", contenido)

        h1 = protocolos.count("'h1'")
        h2 = protocolos.count("'h2'")
        h3 = protocolos.count("'h3'")

        if h1 + h2 + h3 == 0:
            return None

        return {
            "url": url.strip(),
            "H1": h1,
            "H2": h2,
            "H3": h3,
            "secuencia": " ".join(protocolos)
        }

    except Exception as e:
        print(f"[ERROR procesando línea] {linea[:120]}")
        print(e)
        return None


print("Buscando archivos...")

archivos = glob.glob(os.path.join(CARPETA, "**/*"), recursive=True)
archivos = [a for a in archivos if os.path.isfile(a)]

print(f"Archivos encontrados: {len(archivos)}")

for archivo in archivos:
    with open(archivo, "r", encoding="utf-8", errors="ignore") as f:
        lineas = f.readlines()

    for i, linea in enumerate(lineas):
        linea = linea.strip()

        if "H123-compact:" in linea:
            if i + 1 < len(lineas):
                resultado = procesar_linea_compact(lineas[i + 1].strip())

                if resultado is not None:
                    resultado["archivo"] = os.path.basename(archivo)
                    datos.append(resultado)


print(f"Registros H123-compact encontrados: {len(datos)}")

if len(datos) == 0:
    print("No se ha encontrado ningún H123-compact.")
    exit(1)


df = pd.DataFrame(datos)

print("\nResumen:")
print(f"Total de accesos: {len(df)}")
print(f"URLs distintas: {df['url'].nunique()}")

# ------------------------------------------------------------
# Separación visual de puntos repetidos
# ------------------------------------------------------------
np.random.seed(42)

JITTER = 0.18

df["H1_plot"] = df["H1"] + np.random.uniform(-JITTER, JITTER, size=len(df))
df["H2_plot"] = df["H2"] + np.random.uniform(-JITTER, JITTER, size=len(df))
df["H3_plot"] = df["H3"] + np.random.uniform(-JITTER, JITTER, size=len(df))

df.to_csv(SALIDA_CSV, index=False)

# ------------------------------------------------------------
# Crear gráfico 3D grande
# ------------------------------------------------------------
fig = px.scatter_3d(
    df,
    x="H1_plot",
    y="H2_plot",
    z="H3_plot",
    color="url",
    hover_data={
        "url": True,
        "archivo": True,
        "H1": True,
        "H2": True,
        "H3": True,
        "H1_plot": False,
        "H2_plot": False,
        "H3_plot": False,
        "secuencia": True
    },
    title="HOLMES - Visualización 3D ampliada de firmas H123-compact",
    width=1800,
    height=1100
)

fig.update_traces(
    marker=dict(
        size=8,
        opacity=0.80
    )
)

fig.update_layout(
    scene=dict(
        xaxis=dict(
            title="H1 - nº recursos HTTP/1.1",
            dtick=1
        ),
        yaxis=dict(
            title="H2 - nº recursos HTTP/2",
            dtick=1
        ),
        zaxis=dict(
            title="H3 - nº recursos HTTP/3",
            dtick=1
        ),
        aspectmode="cube"
    ),
    legend_title="URL",
    margin=dict(l=0, r=0, b=0, t=60)
)

fig.write_html(SALIDA_HTML)

print("\nCSV generado en:")
print(SALIDA_CSV)

print("\nHTML generado correctamente en:")
print(SALIDA_HTML)
