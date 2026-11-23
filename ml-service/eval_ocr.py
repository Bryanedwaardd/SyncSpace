import sys, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from ocr import read_image
from receipt_parser import extract_total

rows = list(csv.DictReader(open("receipts/labels.csv", encoding="utf-8")))
for mode in ["raw", "gray", "clahe", "adaptive"]:
    benar = 0
    for r in rows:
        text = read_image(f"receipts/{r['filename']}", mode)
        if extract_total(text) == int(r["total"]):
            benar += 1
    print(f"{mode:9} {benar}/{len(rows)} = {benar/len(rows):.0%}")