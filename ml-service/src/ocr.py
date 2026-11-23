"""OCR struk (gambar -> teks) dengan preprocessing + perakitan baris."""
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageOps

try:
    from .preprocess import preprocess
except ImportError:
    from preprocess import preprocess


@lru_cache(maxsize=1)
def _get_reader():
    import easyocr
    return easyocr.Reader(["id", "en"], gpu=False)


def _group_rows(results) -> list[str]:
    """results: [(bbox, text, conf)] -> list baris teks, kiri ke kanan."""
    items = []
    for bbox, text, conf in results:
        ys = [p[1] for p in bbox]
        xs = [p[0] for p in bbox]
        items.append({"text": text, "x": min(xs),
                      "yc": sum(ys) / len(ys), "h": max(ys) - min(ys)})
    items.sort(key=lambda d: d["yc"])

    rows: list[dict] = []
    for it in items:
        # satu baris = pusat vertikalnya berdekatan dengan baris terakhir
        if rows and abs(it["yc"] - rows[-1]["yc"]) < 0.6 * max(it["h"], rows[-1]["h"]):
            r = rows[-1]
            r["items"].append(it)
            r["yc"] = sum(i["yc"] for i in r["items"]) / len(r["items"])
            r["h"] = max(r["h"], it["h"])
        else:
            rows.append({"yc": it["yc"], "h": it["h"], "items": [it]})

    return ["  ".join(i["text"] for i in sorted(r["items"], key=lambda d: d["x"]))
            for r in rows]


def read_image(image_path: str, mode: str = "clahe", debug: bool = False) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File gambar tidak ditemukan: {image_path}")

    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img).convert("RGB")   # putar sesuai EXIF
    arr = preprocess(np.array(img), mode)

    if debug:  # simpan gambar hasil preprocessing biar bisa dilihat mata
        import cv2
        cv2.imwrite("debug_preprocessed.png", arr if arr.ndim == 2
                    else cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))

    results = _get_reader().readtext(arr, detail=1, paragraph=False)
    if debug:
        for _bbox, text, conf in results:
            print(f"  conf={conf:.2f}  {text!r}")

    return "\n".join(_group_rows(results))


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "clahe"
    sys.stdout.reconfigure(encoding="utf-8")
    print(read_image(path, mode, debug=True))