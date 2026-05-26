import os
import glob
import re
import pandas as pd
import plotly.express as px

CARPETA = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/graficas/20accesos_csv_label"
SALIDA_HTML = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/graficas/holmes_3d_interactivo.html"

datos = []


def procesar_linea_compact(linea):
    """
    Lee una línea H123-compact y cuenta cuántos recursos h1, h2 y h3 aparecen.
    No usa ast.literal_eval porque algunas líneas están mal formateadas.
    """

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

print("\nPrimeros registros:")
print(df.head())

print("\nResumen:")
print(f"Total de accesos: {len(df)}")
print(f"URLs distintas: {df['url'].nunique()}")

print("\nURLs encontradas:")
print(df["url"].value_counts())


fig = px.scatter_3d(
    df,
    x="H1",
    y="H2",
    z="H3",
    color="url",
    hover_data=["url", "archivo", "H1", "H2", "H3", "secuencia"],
    title="HOLMES - Visualización 3D de firmas H123-compact"
)

fig.update_traces(
    marker=dict(
        size=6,
        opacity=0.75
    )
)

fig.update_layout(
    scene=dict(
        xaxis_title="H1 - nº recursos HTTP/1.1",
        yaxis_title="H2 - nº recursos HTTP/2",
        zaxis_title="H3 - nº recursos HTTP/3"
    ),
    legend_title="URL"
)

fig.write_html(SALIDA_HTML)

print("\nHTML generado correctamente en:")
print(SALIDA_HTML)
