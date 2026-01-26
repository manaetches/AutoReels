import os
import csv

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'Calm_ADHD_Blueprint_Hooks.csv')
target_dir = r"D:\reels-dev\mixkit\women\family\ADHD_output_reel"

video_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith('.mp4')])

with open(csv_file, 'r', encoding='utf-8', newline='') as f:
    rows = list(csv.reader(f))

header = rows[0]
if 'FilePath' not in header:
    header.append('FilePath')
    for i in range(1, len(rows)):
        if len(rows[i]) < len(header):
            rows[i].extend([''] * (len(header) - len(rows[i])))

fp_index = header.index('FilePath')

for i, vf in enumerate(video_files[:len(rows)-1]):
    row_idx = i + 1
    rows[row_idx][fp_index] = os.path.join(target_dir, vf)

with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerows(rows)

print('Updated CSV with', len(video_files[:len(rows)-1]), 'filepaths')