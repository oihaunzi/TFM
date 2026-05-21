import os
import csv
import re

dir_in = "20accesos"
dir_out = "20accesos_csv_label"
labels_file = "/RAID5-22TB/ohiane.unzilla/x20v9/id_label.txt"

os.makedirs(dir_out, exist_ok=True)

id_to_label = {}

with open(labels_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            id_to_label[parts[0]] = parts[1]

for filename in sorted(os.listdir(dir_in)):
    if not filename.endswith(".txt"):
        continue

    match = re.search(r"captura_(\d+)_H123\.txt", filename)
    if not match:
        continue

    sample_id = match.group(1)
    label = id_to_label.get(sample_id)

    if label is None:
        print(f"[AVISO] Sin label para {filename}")
        continue

    input_path = os.path.join(dir_in, filename)
    output_name = filename.replace(".txt", ".csv")
    output_path = os.path.join(dir_out, output_name)

    with open(input_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(output_path, "w", newline="", encoding="utf-8") as fout:

        writer = csv.writer(fout)
        writer.writerow(["label", "num_resources", "protocols"])

        for line in fin:
            line = line.strip()

            if not line:
                continue

            # Divide cada fila original por coma
            parts = line.split(",", 1)

            if len(parts) == 2:
                num_resources = parts[0].strip()
                protocols = parts[1].strip()
                writer.writerow([label, num_resources, protocols])
            else:
                writer.writerow([label, line])

    print(f"{filename} -> {output_name}")

print("Conversión terminada.")
