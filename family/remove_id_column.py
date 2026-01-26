import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p, 'r', encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))
    old_fields = list(rows[0].keys()) if rows else []

# Desired header (no ID, no URL)
new_fields = ['Hook','Hashtags','LongTailKeywords','FilePath']

# If CSV already in desired shape, do nothing
if old_fields == new_fields:
    print('CSV already has desired header; no change.')
    raise SystemExit(0)

# Rebuild rows with new header order
new_rows = []
for r in rows:
    new_rows.append({k: (r.get(k) or '') for k in new_fields})

with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=new_fields)
    w.writeheader()
    for r in new_rows:
        w.writerow(r)

print('Removed ID/URL columns (if present) and rewrote CSV header to:', new_fields)
