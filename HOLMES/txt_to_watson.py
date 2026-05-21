import os
import re
import csv
import ast
import sys
from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url.strip())
    if parsed.netloc:
        return parsed.netloc
    return url.replace("https://", "").replace("http://", "").strip("/")


def load_log_mapping(log_path):
    """
    Lee log.txt y construye:
        '0000001' -> 'google.com'
        '0000002' -> 'microsoft.com'
    """
    mapping = {}

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("Cancelamos"):
                continue

            parts = line.split()

            # Esperamos al menos:
            # 1 0000001 01 https://google.com ...
            if len(parts) < 4:
                continue

            # El ID bueno es el segundo campo
            group_id = parts[1].strip()
            url = parts[3].strip()

            if not group_id.isdigit():
                continue
            if not url.startswith("http"):
                continue

            # Guardamos solo la primera vez
            if group_id not in mapping:
                mapping[group_id] = normalize_url(url)

    return mapping


def http_to_numeric(http_list):
    conv = {
        "h1": 1,
        "h2": 2,
        "h3": 3
    }
    return [conv.get(x, 0) for x in http_list]


def extract_all_h123_compact(txt_path):
    samples = []

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f]

    for i, line in enumerate(lines):
        if line == "H123-compact:" and i + 1 < len(lines):
            next_line = lines[i + 1]

            if next_line.startswith("(") and next_line.endswith(")"):
                try:
                    data = ast.literal_eval(next_line)
                    wfp = data[0]
                    http_versions = data[1]

                    if isinstance(wfp, list) and isinstance(http_versions, list):
                        samples.append((wfp, http_to_numeric(http_versions)))
                except Exception as e:
                    print(f"[PARSE ERROR] {txt_path}: {e}")

    return samples


def extract_group_id_from_filename(filename):
    m = re.match(r"captura_(\d+)_H123\.txt$", filename)
    if m:
        return m.group(1)
    return None


def build_dataset(txt_dir, log_path, output_csv):
    mapping = load_log_mapping(log_path)

    print(f"IDs cargados desde log: {len(mapping)}")
    print("Primeros IDs del log:", list(mapping.keys())[:10])

    rows = []
    missing = []
    empty = []

    for filename in sorted(os.listdir(txt_dir)):
        if not filename.endswith(".txt"):
            continue
        if not filename.startswith("captura_"):
            continue

        group_id = extract_group_id_from_filename(filename)
        if group_id is None:
            continue

        if group_id not in mapping:
            missing.append((filename, group_id))
            continue

        label = mapping[group_id]
        txt_path = os.path.join(txt_dir, filename)

        samples = extract_all_h123_compact(txt_path)

        if not samples:
            empty.append(filename)
            continue

        for wfp, http_numeric in samples:
            rows.append([label, str(wfp), str(http_numeric)])

        print(f"{filename} -> {label} -> {len(samples)} muestras")

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print("\n==============================")
    print(f"CSV generado: {output_csv}")
    print(f"Total de filas: {len(rows)}")

    if missing:
        print("\nArchivos sin correspondencia en log:")
        for fname, gid in missing[:20]:
            print(f" - {fname} -> {gid}")
        if len(missing) > 20:
            print(f" ... y {len(missing)-20} más")

    if empty:
        print("\nArchivos sin H123-compact válido:")
        for fname in empty[:20]:
            print(f" - {fname}")
        if len(empty) > 20:
            print(f" ... y {len(empty)-20} más")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso:")
        print("python3 txt_to_watson_ok.py <directorio_txt> <log.txt> <salida.csv>")
        sys.exit(1)

    txt_dir = sys.argv[1]
    log_path = sys.argv[2]
    output_csv = sys.argv[3]

    build_dataset(txt_dir, log_path, output_csv)
