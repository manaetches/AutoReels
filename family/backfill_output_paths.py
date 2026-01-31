#!/usr/bin/env python3
import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks2.csv")
output_dir = os.path.join(script_dir, "output_reel")

rows = []
original_fieldnames = None
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh)
        original_fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)
else:
    print("CSV not found, nothing to backfill")
    raise SystemExit(1)

# map files by leading ID (before first underscore)
files = []
if os.path.isdir(output_dir):
    files = [f for f in os.listdir(output_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

file_map = {}
for f in files:
    id_part = f.split('_', 1)[0]
    file_map[id_part] = os.path.join(output_dir, f)

updated = False
for r in rows:
    rid = (r.get('ID') or '').strip()
    if not rid:
        continue
    if rid in file_map:
        path = file_map[rid]
        if r.get('FilePath') != path:
            r['FilePath'] = path
            updated = True

if updated:
    # determine fieldnames, ensuring FilePath is 5th column
    if original_fieldnames:
        fns = list(original_fieldnames)
    else:
        fns = list(rows[0].keys())

    if 'FilePath' not in fns:
        insert_index = 4 if len(fns) >= 4 else len(fns)
        fns.insert(insert_index, 'FilePath')

    with open(csv_file_path, mode='w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=fns)
        writer.writeheader()
        for r in rows:
            out = {k: r.get(k, '') for k in fns}
            writer.writerow(out)
    print(f"Backfilled {csv_file_path} with {len(file_map)} output paths")
else:
    print("No updates required; FilePath values already set or no matching outputs found.")
