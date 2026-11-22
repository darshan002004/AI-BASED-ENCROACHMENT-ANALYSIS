import csv
from pathlib import Path
from collections import Counter

csv_path = Path('C:/Users/Darshan B/.gemini/antigravity/scratch/encrowatch-ai/ENCROWATCH_PILOT_DATASET_MANIFEST.csv')
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = list(csv.DictReader(f))

res_counts = Counter(f"{r['width']}x{r['height']}" for r in reader)
print("Resolution breakdown of all 66 unique images:")
for res, cnt in res_counts.most_common():
    print(f"  {res}: {cnt} images")

# How many images if threshold is width >= 150?
thresh_150 = [r for r in reader if int(r['width']) >= 150]
print(f"\nImages with width >= 150 px: {len(thresh_150)}")

thresh_200 = [r for r in reader if int(r['width']) >= 200]
print(f"Images with width >= 200 px: {len(thresh_200)}")

# Check thumbnails
thumbs = [r for r in reader if int(r['width']) < 100]
print(f"Tiny thumbnails (<100px): {len(thumbs)}")
for t in thumbs:
    print(f"  {t['filename']} ({t['width']}x{t['height']})")
