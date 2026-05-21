import csv
import os
import ast

input_file = "/RAID5-22TB/ohiane.unzilla/x20v9/dataset_h123.txt"
output_file = "/RAID5-22TB/ohiane.unzilla/x20v9/h123_dataset.csv"

rows_written = 0
rows_skipped = 0

with open(input_file, "r", encoding="utf-8") as f_in, \
     open(output_file, "w", newline="", encoding="utf-8") as f_out:

    writer = csv.writer(f_out)

    for line in f_in:
        line = line.strip()
        if not line:
            continue

        filepath, label = line.split(maxsplit=1)

        if not os.path.isfile(filepath):
            print(f"[NO EXISTE] {filepath}")
            rows_skipped += 1
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f]

        for i in range(len(lines)):
            if lines[i] == "H123-compact:":
                if i + 1 >= len(lines):
                    continue

                try:
                    data = ast.literal_eval(lines[i + 1])
                    wfp = data[0]
                    httpv = data[1]

                    writer.writerow([label, str(wfp), str(httpv)])
                    rows_written += 1

                except Exception as e:
                    print(f"[ERROR PARSE] {filepath} línea {i}")
                    rows_skipped += 1

print(f"Filas escritas: {rows_written}")
print(f"Filas descartadas: {rows_skipped}")
print(f"CSV generado en: {output_file}")
