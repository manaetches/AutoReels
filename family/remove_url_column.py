import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p, 'r', encoding='utf-8', newline='') as f:
    r = list(csv.DictReader(f))
    fieldnames = list(r[0].keys()) if r else []

if 'URL' not in fieldnames:
    print('No URL column found; nothing to do.')
    raise SystemExit(0)

new_fieldnames = [fn for fn in fieldnames if fn != 'URL']
for row in r:
    if 'URL' in row:
        row.pop('URL', None)

with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=new_fieldnames)
    w.writeheader()
    for row in r:
        w.writerow(row)

print('Removed URL column from CSV and rewrote file.')
