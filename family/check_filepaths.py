import csv
p = r'c:\xampp\htdocs\autoVideoPosts\reels-dev\family\Calm_ADHD_Blueprint_Hooks.csv'
with open(p,'r',encoding='utf-8',newline='') as f:
    r = csv.DictReader(f)
    print('Fields:', r.fieldnames)
    for i,row in enumerate(r, start=1):
        if i>10: break
        print(i, row.get('ID',''), repr(row.get('FilePath','')))
