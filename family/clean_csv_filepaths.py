import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p, 'r', encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else ['Hook','Hashtags','LongTailKeywords','FilePath']

if 'FilePath' not in fieldnames:
    fieldnames.append('FilePath')
if 'URL' not in fieldnames:
    fieldnames.append('URL')

changed = 0
for r in rows:
    fp = (r.get('FilePath') or '').strip()
    url = (r.get('URL') or '').strip()
    if not fp and url:
        r['FilePath'] = url
        changed += 1
    # if both present, prefer FilePath; nothing to change except clear URL
    if url:
        r['URL'] = ''

with open(p, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Cleaned CSV: cleared URL and ensured FilePath present for {len(rows)} rows (moved {changed} values).")
