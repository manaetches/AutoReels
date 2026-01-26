import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p, 'r', encoding='utf-8', newline='') as f:
    rows = list(csv.reader(f))
if not rows:
    print('empty')
    raise SystemExit(0)
header = rows[0]
# if ID already present, do nothing
if header and header[0] == 'ID':
    print('ID column already present')
    raise SystemExit(0)
new_header = ['ID'] + header
new_rows = [new_header]
for i, r in enumerate(rows[1:], start=1):
    new_rows.append([str(i)] + r)
with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerows(new_rows)
print('Added ID column to CSV, rows:', len(new_rows)-1)
