import os
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(BASE_DIR, "resultados", "puntos_3d_H123_sin_outliers.csv")

OUTPUT_PREDICCIONES = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_geometrico_sin_outliers_predicciones.csv"
)

OUTPUT_RESUMEN = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_geometrico_sin_outliers_resumen.txt"
)

TRAIN_RATIO = 0.8


df = pd.read_csv(INPUT_CSV)
df = df.dropna(subset=["url", "H1", "H2", "H3"])

train_parts = []
test_parts = []

for url, grupo in df.groupby("url"):
    grupo = grupo.reset_index(drop=True)

    if len(grupo) < 2:
        continue

    n_train = int(len(grupo) * TRAIN_RATIO)

    if n_train >= len(grupo):
        n_train = len(grupo) - 1

    if n_train < 1:
        continue

    train_parts.append(grupo.iloc[:n_train])
    test_parts.append(grupo.iloc[n_train:])

train_df = pd.concat(train_parts, ignore_index=True)
test_df = pd.concat(test_parts, ignore_index=True)

X_train = train_df[["H1", "H2", "H3"]].values
y_train = train_df["url"].values

X_test = test_df[["H1", "H2", "H3"]].values
y_test = test_df["url"].values

predicciones = []

for punto_test, url_real in zip(X_test, y_test):
    distancias = np.linalg.norm(X_train - punto_test, axis=1)

    idx_min = np.argmin(distancias)

    url_predicha = y_train[idx_min]
    distancia_minima = distancias[idx_min]

    predicciones.append({
        "url_real": url_real,
        "url_predicha": url_predicha,
        "acierto": url_real == url_predicha,
        "distancia_minima": distancia_minima,
        "H1_test": punto_test[0],
        "H2_test": punto_test[1],
        "H3_test": punto_test[2]
    })

pred_df = pd.DataFrame(predicciones)

accuracy = accuracy_score(
    pred_df["url_real"],
    pred_df["url_predicha"]
)

os.makedirs(os.path.dirname(OUTPUT_PREDICCIONES), exist_ok=True)

pred_df.to_csv(OUTPUT_PREDICCIONES, index=False)

with open(OUTPUT_RESUMEN, "w") as f:
    f.write("CLASIFICADOR GEOMÉTRICO 1-NN SIN OUTLIERS\n")
    f.write("=========================================\n\n")
    f.write(f"Archivo de entrada: {INPUT_CSV}\n")
    f.write(f"Muestras totales: {len(df)}\n")
    f.write(f"Muestras train: {len(train_df)}\n")
    f.write(f"Muestras test: {len(test_df)}\n")
    f.write(f"Train ratio: {TRAIN_RATIO}\n\n")
    f.write(f"Accuracy geométrico sin outliers: {accuracy:.4f}\n")
    f.write(f"Accuracy geométrico sin outliers (%): {accuracy * 100:.2f}%\n\n")
    f.write("Classification report:\n")
    f.write(classification_report(
        pred_df["url_real"],
        pred_df["url_predicha"],
        zero_division=0
    ))

print("\nCLASIFICADOR GEOMÉTRICO 1-NN SIN OUTLIERS")
print("=========================================")
print(f"Archivo: {INPUT_CSV}")
print(f"Muestras totales: {len(df)}")
print(f"Train: {len(train_df)}")
print(f"Test: {len(test_df)}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Accuracy (%): {accuracy * 100:.2f}%")

print(f"\nPredicciones guardadas en: {OUTPUT_PREDICCIONES}")
print(f"Resumen guardado en: {OUTPUT_RESUMEN}")
