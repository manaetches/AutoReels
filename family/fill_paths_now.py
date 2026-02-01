#!/usr/bin/env python3
import csv, os
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'Calm_ADHD_Blueprint_Hooks2.csv')
out_dir = os.path.join(script_dir, 'output_reel')
if not os.path.isfile(csv_file):
    print('CSV missing:', csv_file); raise SystemExit(1)
rows = []
with open(csv_file, 'r', encoding='utf-8', newline='') as fh:
    r = csv.DictReader(fh)
    orig = r.fieldnames
    for row in r:
        rows.append(row)
files = {}
if os.path.isdir(out_dir):
    for f in os.listdir(out_dir):
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            idp = f.split('_',1)[0]
            files[idp]=os.path.abspath(os.path.join(out_dir, f))
updated=False
for row in rows:
    rid = (row.get('ID') or '').strip()
    if rid and rid in files:
        if (row.get('FilePath') or '').strip() != files[rid]:
            row['FilePath']=files[rid]
            updated=True
if updated:
    # prepare fieldnames with FilePath at index 4
    if orig:
        base = [fn for fn in orig if fn!='FilePath']
    else:
        base=list(rows[0].keys())
    insert_index = 4 if len(base)>=4 else len(base)
    fns=list(base)
    if 'FilePath' in fns: fns.remove('FilePath')
    fns.insert(insert_index,'FilePath')
    tmp=csv_file+'.tmp'
    with open(tmp,'w',encoding='utf-8',newline='') as wf:
        w=csv.DictWriter(wf,fieldnames=fns)
        w.writeheader()
        for r in rows:
            out={k:r.get(k,'') for k in fns}
            out['FilePath']=os.path.abspath(out.get('FilePath') or '')
            w.writerow(out)
    os.replace(tmp,csv_file)
    print('Updated CSV',csv_file)
else:
    print('No updates needed')
