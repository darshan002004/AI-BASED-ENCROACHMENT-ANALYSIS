import csv
import json
from pathlib import Path
from collections import defaultdict

csv_path = Path('C:/Users/Darshan B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_PILOT_DATASET_MANIFEST.csv')
with open(csv_path, 'r', encoding='utf-8') as f:
    all_rows = list(csv.DictReader(f))

# Rank candidates by resolution (width * height), size, and unburnt status (prefer original/privacy over annotated)
def get_rank(r):
    w, h = int(r['width']), int(r['height'])
    area = w * h
    folder = r['folder']
    folder_pref = 2 if folder == 'original' else (1 if folder in ['privacy', '.'] else 0)
    return (area, folder_pref, float(r['size_kb']))

sorted_all = sorted(all_rows, key=get_rank, reverse=True)

# Select top 42
selected_42 = sorted_all[:42]

print(f"Selected {len(selected_42)} images:")
print(f"Max resolution: {selected_42[0]['width']}x{selected_42[0]['height']}")
print(f"Min resolution: {selected_42[-1]['width']}x{selected_42[-1]['height']}")

# Breakdown of selected 42
by_folder = defaultdict(int)
by_res = defaultdict(int)
for r in selected_42:
    by_folder[r['folder']] += 1
    by_res[f"{r['width']}x{r['height']}"] += 1

print("\nBy Folder:")
for k, v in by_folder.items():
    print(f"  {k}: {v}")

print("\nBy Resolution:")
for k, v in by_res.items():
    print(f"  {k}: {v}")
