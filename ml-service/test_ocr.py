"""Tes OCR struk end-to-end: gambar -> teks -> {kategori, total}."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from ocr import read_image                 # noqa: E402
from receipt_parser import ReceiptParser   # noqa: E402

image = sys.argv[1] if len(sys.argv) > 1 else "sample_receipt.png"

print("=== OCR ===", flush=True)
text = read_image(image)
print(text, flush=True)

print("\n=== HASIL ===", flush=True)
print(json.dumps(ReceiptParser().parse(text), ensure_ascii=False, indent=2), flush=True)
