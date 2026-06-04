import os
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(BASE_DIR, "resultados", "puntos_3d_H123_sin_outliers.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "resultados", "mapa_3d_H123_sin_outliers_filtrable.html")

df = pd.read_csv(INPUT_CSV)
df.columns = df.columns.str.strip()

fig = px.scatter_3d(
    df,
    x="H1",
    y="H2",
    z="H3",
    color="url",
    hover_data=["url", "archivo", "access_id", "H1", "H2", "H3"],
    title="Mapa 3D de firmas H1-H2-H3 sin outliers",
    labels={
        "H1": "Dimensión 1: número de recursos H1",
        "H2": "Dimensión 2: número de recursos H2",
        "H3": "Dimensión 3: número de recursos H3",
        "url": "URL"
    }
)

fig.update_traces(
    marker=dict(
        size=5,
        opacity=0.75
    )
)

fig.update_layout(
    legend_title_text="URL",
    scene=dict(
        xaxis_title="H1",
        yaxis_title="H2",
        zaxis_title="H3"
    )
)

fig.write_html(OUTPUT_HTML)

print(f"[OK] Mapa 3D sin outliers generado: {OUTPUT_HTML}")
print(f"[INFO] Total puntos sin outliers: {len(df)}")
print(f"[INFO] Total URLs: {df['url'].nunique()}")
