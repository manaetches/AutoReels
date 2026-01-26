import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p, 'r', encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))

if not rows:
    print('CSV empty, nothing to do')
    raise SystemExit(0)

old_fieldnames = list(rows[0].keys())
if 'ID' not in old_fieldnames:
    fieldnames = ['ID'] + [k for k in old_fieldnames if k != 'ID']
else:
    fieldnames = old_fieldnames

changed = 0
for i, r in enumerate(rows):
    if not (r.get('ID') or '').strip():
        r['ID'] = str(i+1)
        changed += 1

with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f'Assigned IDs to CSV rows (added {changed} IDs).')
