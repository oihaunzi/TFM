import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_watson_resumen.csv"
)

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "resultados",
    "accuracy_watson_resumen_porcentajes.csv"
)

df = pd.read_csv(INPUT_CSV)

columnas_accuracy = [
    "media_accuracy",
    "desv_tipica_accuracy",
    "min_accuracy",
    "max_accuracy",
    "mediana_accuracy"
]

for col in columnas_accuracy:
    if col in df.columns:
        df[col + "_porcentaje"] = df[col] * 100

df.to_csv(OUTPUT_CSV, index=False)

print("\nTABLA WATSON EN PORCENTAJES\n")
print(df)

print(f"\nGuardado en: {OUTPUT_CSV}")
