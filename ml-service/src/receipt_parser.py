"""
Parser struk belanja: dari teks hasil OCR -> {category, total}.

Fokus: cukup tahu struk ini masuk KATEGORI apa dan TOTAL-nya berapa.

Strategi:
  TOTAL    -> cari baris "total" (toleran salah baca OCR seperti 'Tota)'),
              bukan 'subtotal' dan bukan 'total qty'. Fallback: angka terbesar
              tanpa baris tunai/kembali/bayar/telp.
  CATEGORY -> (1) nama merchant (persis, lalu mirip-mirip untuk salah baca OCR),
              (2) kata kunci isi struk, (3) kalau tidak yakin, classifier NLP.
"""

import re
from difflib import SequenceMatcher
from pathlib import Path

import joblib

try:
    from .amount_parser import normalize_spoken_numbers
    from .train import clean_text
except ImportError:
    from amount_parser import normalize_spoken_numbers
    from train import clean_text

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

# kata kunci -> kategori (dari nama toko / isi struk yang khas)
_MERCHANT_KEYWORDS = {
    "Makanan & Minuman": [
        "resto", "restaurant", "cafe", "kafe", "coffee", "kopi", "starbucks",
        "kfc", "mcd", "mcdonald", "burger", "pizza", "warteg", "warung", "bakso",
        "ayam", "nasi", "mie", "bakery", "roti", "donut", "chatime", "kebab",
        "food", "dimsum", "sate", "geprek", "janji jiwa", "kopi kenangan",
        "jus", "dine in", "takeaway", "take away", "meja", "pesanan",
        "minum", "makan",
    ],
    "Belanja": [
        "indomaret", "alfamart", "alfamidi", "superindo", "hypermart", "giant",
        "transmart", "carrefour", "supermarket", "minimarket", "mall", "store",
        "shop", "fashion", "uniqlo", "matahari", "ramayana", "watsons", "guardian",
        "shopee", "tokopedia", "lazada",
    ],
    "Transport": [
        "pertamina", "shell", "spbu", "bensin", "pertalite", "pertamax", "solar",
        "parkir", "parking", "tol", "gojek", "grab", "bluebird", "taksi", "oli",
        "bengkel", "servis motor", "cuci",
    ],
    "Tagihan": [
        "pln", "listrik", "pdam", "indihome", "telkom", "wifi", "pulsa", "paket data",
        "bpjs", "asuransi", "cicilan", "angsuran",
    ],
    "Hiburan": [
        "cgv", "xxi", "cinema", "bioskop", "cinepolis", "timezone", "karaoke",
        "steam", "netflix", "spotify", "game", "tiket",
    ],
    "Pendidikan": [
        "toko buku", "gramedia", "gunung agung", "fotokopi", "percetakan", "kampus",
        "universitas", "sekolah", "kursus", "bimbel",
    ],
    "Lainnya": [
        "apotek", "apotik", "kimia farma", "klinik", "rumah sakit",
        "laundry", "salon", "barbershop", "pangkas",
    ],
}

# brand merchant yang sangat menentukan kategori (menang telak bila cocok)
_STRONG_MERCHANTS = {
    "indomaret": "Belanja", "alfamart": "Belanja", "alfamidi": "Belanja",
    "superindo": "Belanja", "hypermart": "Belanja", "transmart": "Belanja",
    "carrefour": "Belanja", "giant": "Belanja", "uniqlo": "Belanja",
    "matahari": "Belanja", "watsons": "Belanja", "guardian": "Belanja",
    "starbucks": "Makanan & Minuman", "kfc": "Makanan & Minuman",
    "mcdonald": "Makanan & Minuman", "mcd": "Makanan & Minuman",
    "pizza": "Makanan & Minuman", "chatime": "Makanan & Minuman",
    "janji jiwa": "Makanan & Minuman", "kopi kenangan": "Makanan & Minuman",
    "pertamina": "Transport", "shell": "Transport", "spbu": "Transport",
    "cgv": "Hiburan", "xxi": "Hiburan", "cinepolis": "Hiburan",
    "timezone": "Hiburan", "gramedia": "Pendidikan",
    "kimia farma": "Lainnya", "apotek": "Lainnya", "apotik": "Lainnya",
}

# baris yang BUKAN total belanja. "kemba" sengaja dipotong karena OCR
# sering memecah "Kemba ] i"
_SKIP_WORDS = ("tunai", "cash", "kembali", "kemba", "change", "bayar",
               "npwp", "telp", "tel.", "kartu", "debit", "kredit")

# huruf yang sering salah dibaca OCR sebagai angka
_OCR_DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1",
                                "|": "1", "S": "5", "B": "8"})


def _fix_numeric_tokens(s: str) -> str:
    """Koreksi huruf yang salah baca jadi angka, hanya pada token yang
    sebagian besar berisi angka (supaya kata biasa tidak ikut rusak)."""
    s = re.sub(r"(?i)rp\.?", " ", s)
    out = []
    for tok in s.split():
        digits = sum(c.isdigit() for c in tok)
        if digits >= 2 and digits >= len(tok) / 2:
            tok = tok.translate(_OCR_DIGIT_FIX)
        out.append(tok)
    return " ".join(out)


def _clean_number_spacing(s: str) -> str:
    """Rapikan angka yang dipecah OCR."""
    # pemisah ganda/campuran -> satu: "14,,000" dan "38.,000" -> "14.000", "38.000"
    s = re.sub(r"[.,]{2,}", ".", s)
    # spasi di sekitar pemisah: "26 ,620" -> "26,620"
    s = re.sub(r"(\d)\s*([.,])\s*(\d{3})\b", r"\1\2\3", s)
    # ribuan yang terpisah spasi: "22  000" -> "22.000".
    # lookbehind memastikan "000" bukan bagian dari angka yang sudah utuh
    # (kalau tidak, "4.000  000" salah digabung jadi "4.000.000")
    s = re.sub(r"(?<![\d.,])(\d{1,3})\s+(000)\b", r"\1.\2", s)
    return s


def _grab_amount(s: str) -> int | None:
    """Ambil satu angka uang dari sepotong teks struk.

    Di struk, pemisah (titik/koma) yang diikuti tepat 3 digit = pemisah ribuan,
    jadi cukup dibuang. (Beda dengan ucapan "1,5 juta", di mana koma = desimal.)
    """
    t = _clean_number_spacing(_fix_numeric_tokens(s)).lower()
    best = None
    for m in re.finditer(r"\d{1,3}(?:[.,]\d{3})+|\d{3,}", t):
        val = int(re.sub(r"[.,]", "", m.group(0)))
        if 100 <= val < 100_000_000:   # buang qty/angka kecil & nomor panjang
            if best is None or val > best:
                best = val
    return best


def extract_total(text: str) -> int | None:
    """Ambil nilai TOTAL dari teks struk."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    total_candidates: list[int] = []
    for i, ln in enumerate(lines):
        low = ln.lower()
        # "tota" + salah baca huruf terakhir: l / 1 / i / ) / ] / | / !
        is_total = re.search(r"tota[l1i\)\]\|!]", low) is not None
        is_sub = re.search(r"sub\s*tota", low) is not None
        is_qty = "qty" in low or "item" in low
        if is_total and not is_sub and not is_qty:
            val = _grab_amount(ln)
            if val is None and i + 1 < len(lines):
                nxt = lines[i + 1]
                if not any(w in nxt.lower() for w in _SKIP_WORDS):
                    val = _grab_amount(nxt)
            if val is not None:
                total_candidates.append(val)

    if total_candidates:
        return max(total_candidates)

    # fallback: angka terbesar, tanpa baris tunai/kembali/bayar/telp
    all_amounts = []
    for ln in lines:
        if any(w in ln.lower() for w in _SKIP_WORDS):
            continue
        v = _grab_amount(ln)
        if v is not None:
            all_amounts.append(v)
    return max(all_amounts) if all_amounts else None


def _has_word(kw: str, text: str) -> bool:
    """Cocokkan kata utuh, mis. 'oli' tidak cocok dengan 'polisi'."""
    return re.search(rf"\b{re.escape(kw)}\b", text) is not None


def _fuzzy_brand(head: str) -> str | None:
    """Cocokkan nama brand yang salah dibaca OCR, mis. 'altamart' -> 'alfamart'.

    Hanya brand yang cukup panjang (>= 6 huruf): brand pendek seperti 'kfc'
    atau 'xxi' terlalu mudah salah cocok kalau dilonggarkan.
    """
    words = re.findall(r"[a-z]+", head)
    cands = set(words) | {f"{a} {b}" for a, b in zip(words, words[1:])}
    best_cat, best_ratio = None, 0.8          # ambang kemiripan minimal
    for brand, cat in _STRONG_MERCHANTS.items():
        if len(brand) < 6:
            continue
        for c in cands:
            if abs(len(c) - len(brand)) > 2:
                continue
            r = SequenceMatcher(None, c, brand).ratio()
            if r > best_ratio:
                best_cat, best_ratio = cat, r
    return best_cat


def guess_category_by_keyword(text: str) -> str | None:
    """Tebak kategori dari nama merchant / kata kunci struk. None jika tak yakin.

    1) Brand merchant kuat, persis (potongan teks, karena OCR sering
       menempelkan kata). Header dicek dulu, lalu seluruh teks.
    2) Brand merchant di header yang salah baca OCR (fuzzy).
    3) Skor kata kunci umum (kata utuh); 4 baris teratas dibobot 3x.
    """
    low = text.lower()
    head = " ".join(low.splitlines()[:4])

    for brand, cat in _STRONG_MERCHANTS.items():
        if brand in head:
            return cat
    for brand, cat in _STRONG_MERCHANTS.items():
        if brand in low:
            return cat

    cat = _fuzzy_brand(head)
    if cat:
        return cat

    scores: dict[str, float] = {}
    for cat, kws in _MERCHANT_KEYWORDS.items():
        score = 0.0
        for kw in kws:
            if _has_word(kw, head):
                score += 3
            elif _has_word(kw, low):
                score += 1
        if score:
            scores[cat] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


class ReceiptParser:
    def __init__(self, model_dir: Path = MODEL_DIR):
        category_path = model_dir / "category_model.joblib"
        if not category_path.exists():
            raise FileNotFoundError(
                f"Model belum ada di {model_dir}. Jalankan 'python src/train.py' dulu."
            )
        self.category_model = joblib.load(category_path)

    def parse(self, text: str) -> dict:
        """Dari teks struk -> {type, category, total, category_method, raw_text}."""
        total = extract_total(text)

        category = guess_category_by_keyword(text)
        method = "keyword"
        if category is None:
            clean = clean_text(normalize_spoken_numbers(text))
            category = self.category_model.predict([clean])[0]
            method = "model"

        return {
            "type": "pengeluaran",
            "category": category,
            "total": total,
            "category_method": method,
            "raw_text": text,
        }


if __name__ == "__main__":
    import json

    sample = """INDOMARET
    Jl. Merdeka No. 10
    Aqua 600ml        4.000
    Indomie Goreng    3.500
    Chitato           9.500
    Subtotal         17.000
    Total            17.000
    Tunai            20.000
    Kembali           3.000
    """
    parser = ReceiptParser()
    print(json.dumps(parser.parse(sample), ensure_ascii=False, indent=2))