import os
import csv
import math
import pandas as pd
import matplotlib.pyplot as plt
from itertools import combinations
from matplotlib.path import Path

INPUT_CSV = "resultados_fingerprints_2d/fingerprints_interactivo_pca.csv"
OUT_DIR = "resultados_fingerprints_2d/solapamientos"

os.makedirs(OUT_DIR, exist_ok=True)

OUT_PAIRS = os.path.join(OUT_DIR, "pares_solapados.csv")
OUT_SUMMARY = os.path.join(OUT_DIR, "resumen_solapamientos.csv")
OUT_TXT = os.path.join(OUT_DIR, "resumen_solapamientos.txt")
OUT_PNG = os.path.join(OUT_DIR, "top_solapamientos.png")


def convex_hull(points):
    points = sorted(set(points))
    if len(points) <= 2:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def bbox_intersects(b1, b2):
    return not (
        b1[1] < b2[0] or
        b2[1] < b1[0] or
        b1[3] < b2[2] or
        b2[3] < b1[2]
    )


def segments_intersect(p1, p2, q1, q2):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, c):
        return (
            min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and
            min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
        )

    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)

    if o1 * o2 < 0 and o3 * o4 < 0:
        return True

    eps = 1e-9
    if abs(o1) < eps and on_segment(p1, q1, p2):
        return True
    if abs(o2) < eps and on_segment(p1, q2, p2):
        return True
    if abs(o3) < eps and on_segment(q1, p1, q2):
        return True
    if abs(o4) < eps and on_segment(q1, p2, q2):
        return True

    return False


def polygon_intersects(poly1, poly2):
    if len(poly1) < 3 or len(poly2) < 3:
        return False

    if not bbox_intersects(bbox(poly1), bbox(poly2)):
        return False

    # Bordes cruzados
    for i in range(len(poly1)):
        p1 = poly1[i]
        p2 = poly1[(i + 1) % len(poly1)]

        for j in range(len(poly2)):
            q1 = poly2[j]
            q2 = poly2[(j + 1) % len(poly2)]

            if segments_intersect(p1, p2, q1, q2):
                return True

    # Un polígono dentro de otro
    path1 = Path(poly1)
    path2 = Path(poly2)

    if path1.contains_point(poly2[0]):
        return True

    if path2.contains_point(poly1[0]):
        return True

    return False


def centroid(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


df = pd.read_csv(INPUT_CSV)

groups = {}

for label, group in df.groupby("label"):
    points = list(zip(group["x"], group["y"]))
    hull = convex_hull(points)

    groups[label] = {
        "points": points,
        "hull": hull,
        "centroid": centroid(points),
        "num_points": len(points)
    }

pairs = []

labels = sorted(groups.keys())

for label_a, label_b in combinations(labels, 2):
    g1 = groups[label_a]
    g2 = groups[label_b]

    intersects = polygon_intersects(g1["hull"], g2["hull"])
    centroid_distance = distance(g1["centroid"], g2["centroid"])

    if intersects:
        pairs.append({
            "label_1": label_a,
            "label_2": label_b,
            "centroid_distance": centroid_distance,
            "points_1": g1["num_points"],
            "points_2": g2["num_points"]
        })

pairs_df = pd.DataFrame(pairs)

if not pairs_df.empty:
    pairs_df = pairs_df.sort_values("centroid_distance", ascending=True)

pairs_df.to_csv(OUT_PAIRS, index=False)

# Resumen por label
overlap_count = {label: 0 for label in labels}

for _, row in pairs_df.iterrows():
    overlap_count[row["label_1"]] += 1
    overlap_count[row["label_2"]] += 1

summary_rows = []

for label in labels:
    summary_rows.append({
        "label": label,
        "num_solapamientos": overlap_count[label],
        "solapa": "sí" if overlap_count[label] > 0 else "no"
    })

summary_df = pd.DataFrame(summary_rows)
summary_df = summary_df.sort_values("num_solapamientos", ascending=False)
summary_df.to_csv(OUT_SUMMARY, index=False)

total_labels = len(labels)
labels_solapan = sum(1 for v in overlap_count.values() if v > 0)
labels_no_solapan = total_labels - labels_solapan
total_pairs = total_labels * (total_labels - 1) // 2
pairs_solapados = len(pairs_df)
pairs_no_solapados = total_pairs - pairs_solapados

with open(OUT_TXT, "w", encoding="utf-8") as f:
    f.write("RESUMEN DE SOLAPAMIENTOS DE FINGERPRINTS\n")
    f.write("=======================================\n\n")
    f.write(f"Total labels/webs: {total_labels}\n")
    f.write(f"Labels con al menos un solapamiento: {labels_solapan}\n")
    f.write(f"Labels sin solapamientos detectados: {labels_no_solapan}\n\n")
    f.write(f"Total pares posibles: {total_pairs}\n")
    f.write(f"Pares solapados: {pairs_solapados}\n")
    f.write(f"Pares no solapados: {pairs_no_solapados}\n\n")

    f.write("TOP 30 pares solapados más cercanos:\n")
    f.write("-----------------------------------\n")

    if pairs_df.empty:
        f.write("No se han detectado solapamientos.\n")
    else:
        for _, row in pairs_df.head(30).iterrows():
            f.write(
                f"{row['label_1']}  <->  {row['label_2']} "
                f"(distancia centroides={row['centroid_distance']:.4f})\n"
            )

# Gráfico top labels con más solapamientos
top = summary_df.head(30)

plt.figure(figsize=(18, 12))
plt.barh(top["label"], top["num_solapamientos"])
plt.xlabel("Número de solapamientos detectados")
plt.ylabel("Label / web")
plt.title("Top 30 webs con más solapamientos de área PCA")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
plt.close()

print("Generado:")
print(OUT_PAIRS)
print(OUT_SUMMARY)
print(OUT_TXT)
print(OUT_PNG)

print("\nResumen:")
print(f"Labels/webs totales: {total_labels}")
print(f"Labels con solapamiento: {labels_solapan}")
print(f"Labels sin solapamiento: {labels_no_solapan}")
print(f"Pares solapados: {pairs_solapados}")
print(f"Pares no solapados: {pairs_no_solapados}")
