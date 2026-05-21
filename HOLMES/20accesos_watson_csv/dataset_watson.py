import os
import csv
import re

dir_csv_actual = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/HOLMES/20accesos_csv"
labels_file = "/RAID5-22TB/ohiane.unzilla/x20v9/id_label.txt"
output_file = "/RAID5-22TB/ohiane.unzilla/HOLMESWATSON/H123-Website-Fingerprinting/HOLMES/dataset_watson.csv"

id_to_label = {}

with open(labels_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2:
            id_to_label[parts[0]] = parts[1]

with open(output_file, "w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    writer.writerow(["label", "num_resources", "protocols"])

    for filename in sorted(os.listdir(dir_csv_actual)):
        if not filename.endswith(".csv"):
            continue

        match = re.search(r"captura_(\d+)_H123\.csv", filename)
        if not match:
            continue

        sample_id = match.group(1)
        label = id_to_label.get(sample_id)

        if label is None:
            print(f"[AVISO] No hay label para {filename}")
            continue

        ruta_csv = os.path.join(dir_csv_actual, filename)

        nums = []
        protos = []

        with open(ruta_csv, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

            nums = [int(x) for x in re.findall(r"\d+", contenido)]
            protos = re.findall(r"h1|h2|h3|http1|http2|http3|http/1\.1|http/2|http/3", contenido, re.IGNORECASE)

            protos = [
                p.lower()
                 .replace("http/1.1", "h1")
                 .replace("http/2", "h2")
                 .replace("http/3", "h3")
                 .replace("http1", "h1")
                 .replace("http2", "h2")
                 .replace("http3", "h3")
                for p in protos
            ]

        writer.writerow([label, nums, protos])

print(f"Dataset generado en: {output_file}")
