import csv

csv_file_path = "../Calm_ADHD_Blueprint_Hooks.csv"  # Path updated to parent directory

with open(csv_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip header row
    for row in reader:
        print(row)
