import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(BASE_DIR, "resultados", "puntos_3d_H123.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "resultados")

OUTLIERS_RESUMEN = os.path.join(OUTPUT_DIR, "outliers_resumen_por_url.csv")
PUNTOS_CON_MARCA = os.path.join(OUTPUT_DIR, "puntos_3d_H123_con_outliers.csv")
PUNTOS_SIN_OUTLIERS = os.path.join(OUTPUT_DIR, "puntos_3d_H123_sin_outliers.csv")

df = pd.read_csv(INPUT_CSV)
df.columns = df.columns.str.strip()

print("[INFO] Columnas encontradas:")
print(df.columns.tolist())

marcados = []

for url, grupo in df.groupby("url"):
    grupo = grupo.copy()

    for col in ["H1", "H2", "H3"]:
        q1 = grupo[col].quantile(0.25)
        q3 = grupo[col].quantile(0.75)
        iqr = q3 - q1

        limite_inf = q1 - 1.5 * iqr
        limite_sup = q3 + 1.5 * iqr

        grupo[f"outlier_{col}"] = (
            (grupo[col] < limite_inf) |
            (grupo[col] > limite_sup)
        )

    grupo["es_outlier"] = (
        grupo["outlier_H1"] |
        grupo["outlier_H2"] |
        grupo["outlier_H3"]
    )

    marcados.append(grupo)

df_marcado = pd.concat(marcados, ignore_index=True)

df_sin_outliers = df_marcado[df_marcado["es_outlier"] == False].copy()

resumen = (
    df_marcado.groupby("url")
    .agg(
        accesos_originales=("access_id", "count"),
        outliers_eliminados=("es_outlier", "sum")
    )
    .reset_index()
)

resumen["accesos_restantes"] = (
    resumen["accesos_originales"] - resumen["outliers_eliminados"]
)

resumen["porcentaje_eliminado"] = (
    resumen["outliers_eliminados"] / resumen["accesos_originales"] * 100
).round(2)

resumen = resumen.sort_values(
    by=["outliers_eliminados", "porcentaje_eliminado"],
    ascending=False
)

df_marcado.to_csv(PUNTOS_CON_MARCA, index=False)
df_sin_outliers.to_csv(PUNTOS_SIN_OUTLIERS, index=False)
resumen.to_csv(OUTLIERS_RESUMEN, index=False)

print("[OK] Análisis de outliers generado")
print(f"[OK] Puntos con marca: {PUNTOS_CON_MARCA}")
print(f"[OK] Puntos sin outliers: {PUNTOS_SIN_OUTLIERS}")
print(f"[OK] Resumen por URL: {OUTLIERS_RESUMEN}")

print("\nTOP URLs con más outliers:")
print(resumen.head(15))
