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
    file_map[id_part] = os.path.abspath(os.path.join(output_dir, f))

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
    # determine base fieldnames and ensure FilePath is 5th column
    if original_fieldnames:
        base_fns = [fn for fn in original_fieldnames if fn != 'FilePath']
    else:
        base_fns = [k for k in rows[0].keys() if k != 'FilePath']

    insert_index = 4 if len(base_fns) >= 4 else len(base_fns)
    fns = list(base_fns)
    if 'FilePath' in fns:
        fns.remove('FilePath')
    fns.insert(insert_index, 'FilePath')

    tmp_csv = csv_file_path + '.tmp'
    with open(tmp_csv, mode='w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=fns)
        writer.writeheader()
        for r in rows:
            out = {k: r.get(k, '') for k in fns}
            out['FilePath'] = os.path.abspath(out.get('FilePath') or '')
            print(f"Writing CSV row ID={r.get('ID')} FilePath={out['FilePath']}")
            writer.writerow(out)
    try:
        os.replace(tmp_csv, csv_file_path)
        print(f"Backfilled {csv_file_path} with {len(file_map)} output paths")
    except Exception:
        try:
            os.remove(csv_file_path)
        except Exception:
            pass
        os.replace(tmp_csv, csv_file_path)
        print(f"Backfilled (fallback) {csv_file_path} with {len(file_map)} output paths")
else:
    print("No updates required; FilePath values already set or no matching outputs found.")
