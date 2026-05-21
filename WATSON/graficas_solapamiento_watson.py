import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations

INPUT_FILE = "resultados_watson_intra_csv.csv"

OUT_RIDGELINE = "ridgeline_watson_todas.png"
OUT_OVERLAY = "areas_solapadas_top20.png"
OUT_OVERLAPS = "solapamientos_watson.csv"

TOP_N = 20
GRID_SIZE = 800


def parse_runs(value):
    values = []
    for x in str(value).split(";"):
        try:
            values.append(float(x))
        except ValueError:
            pass
    return values


def kde_numpy(values, grid, bandwidth=None):
    values = np.array(values, dtype=float)

    if len(values) == 0:
        return np.zeros_like(grid)

    if bandwidth is None:
        std = np.std(values)
        bandwidth = 1.06 * std * (len(values) ** (-1 / 5)) if std > 0 else 0.01

    bandwidth = max(bandwidth, 0.005)

    density = np.zeros_like(grid)

    for v in values:
        density += np.exp(-0.5 * ((grid - v) / bandwidth) ** 2)

    density /= (len(values) * bandwidth * np.sqrt(2 * np.pi))

    area = np.trapezoid(density, grid)
    if area > 0:
        density /= area

    return density


df = pd.read_csv(INPUT_FILE, sep=None, engine="python")

data = {}

for _, row in df.iterrows():
    label = row["label"]
    values = parse_runs(row["watson_20_runs"])

    if len(values) > 0:
        data[label] = values

all_values = [v for values in data.values() for v in values]

x_min = min(all_values)
x_max = max(all_values)

padding = (x_max - x_min) * 0.1 if x_max > x_min else 0.1
grid = np.linspace(x_min - padding, x_max + padding, GRID_SIZE)

densities = {}

for label, values in data.items():
    densities[label] = kde_numpy(values, grid)

# 1. Ridgeline grande con todas las webs
labels_sorted = sorted(
    data.keys(),
    key=lambda x: np.std(data[x]),
    reverse=True
)

plt.figure(figsize=(28, max(18, len(labels_sorted) * 0.45)))

offset = 0

for label in labels_sorted:
    density = densities[label]

    if density.max() > 0:
        density_scaled = density / density.max()

        plt.fill_between(
            grid,
            offset,
            offset + density_scaled,
            alpha=0.55
        )

        plt.plot(
            grid,
            offset + density_scaled,
            linewidth=1
        )

    plt.text(
        grid[0],
        offset + 0.35,
        label,
        fontsize=8,
        ha="right",
        va="center"
    )

    offset += 1.15

plt.xlabel("Distancia WATSON")
plt.ylabel("Web / label")
plt.title("Áreas de variabilidad intra-clase por sitio web")
plt.yticks([])
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_RIDGELINE, dpi=300)
plt.close()

# 2. Áreas solapadas de las TOP_N webs con mayor desviación
stats = []

for label, values in data.items():
    stats.append({
        "label": label,
        "std": np.std(values),
        "mean": np.mean(values)
    })

stats_df = pd.DataFrame(stats).sort_values("std", ascending=False)
top_labels = stats_df.head(TOP_N)["label"].tolist()

plt.figure(figsize=(30, 16))

for label in top_labels:
    density = densities[label]

    plt.fill_between(
        grid,
        density,
        alpha=0.25,
        label=f"{label} (std={np.std(data[label]):.4f})"
    )

    plt.plot(grid, density, linewidth=1.5)

plt.xlabel("Distancia WATSON")
plt.ylabel("Densidad")
plt.title(f"Solapamiento de áreas WATSON — Top {TOP_N} webs con mayor variabilidad")
plt.legend(fontsize=9, ncol=2)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_OVERLAY, dpi=300)
plt.close()

# 3. Cálculo de solapamiento entre áreas
overlap_rows = []

for label_a, label_b in combinations(data.keys(), 2):
    d1 = densities[label_a]
    d2 = densities[label_b]

    overlap = np.trapezoid(np.minimum(d1, d2), grid)

    overlap_rows.append({
        "label_1": label_a,
        "label_2": label_b,
        "overlap": overlap,
        "mean_1": np.mean(data[label_a]),
        "mean_2": np.mean(data[label_b]),
        "std_1": np.std(data[label_a]),
        "std_2": np.std(data[label_b])
    })

overlap_df = pd.DataFrame(overlap_rows)
overlap_df = overlap_df.sort_values("overlap", ascending=False)

overlap_df.to_csv(OUT_OVERLAPS, index=False)

print("Generado:")
print(OUT_RIDGELINE)
print(OUT_OVERLAY)
print(OUT_OVERLAPS)
