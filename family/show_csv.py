import csv
p='c:/xampp/htdocs/autoVideoPosts/reels-dev/family/Calm_ADHD_Blueprint_Hooks.csv'
with open(p,'r',encoding='utf-8',newline='') as f:
    r=list(csv.reader(f))
for i in range(4):
    print(i, r[i])
