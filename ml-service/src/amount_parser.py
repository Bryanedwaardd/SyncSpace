"""
Ekstraksi nominal uang dari teks bahasa Indonesia.

Mendukung format umum seperti:
- "10 ribu", "10rb", "10k"      -> 10000
- "1,5 juta" / "1.5 juta"       -> 1500000
- "2 juta"                      -> 2000000
- "Rp10.000" / "Rp 10,000"      -> 10000
- "50000" / "50.000"            -> 50000
- "3500"                        -> 3500

Modul ini sengaja rule-based (bukan ML) karena ekstraksi angka jauh lebih
andal dan deterministik dengan aturan dibanding model statistik.
"""

import re

# urutan penting: cek satuan paling besar lebih dulu
_UNIT_MULTIPLIER = [
    (r"miliar|milyar|m(?![a-z])", 1_000_000_000),
    (r"juta|jt", 1_000_000),
    (r"ribu|rb|k(?![a-z])", 1_000),
]


def _to_float(num_str: str) -> float:
    """Ubah string angka Indonesia menjadi float.

    Menangani pemisah ribuan (titik) dan desimal (koma), serta variasi
    seperti "1.500.000", "1,5", "10.000".
    """
    s = num_str.strip()

    has_comma = "," in s
    has_dot = "." in s

    if has_comma and has_dot:
        # pola Indonesia: titik = ribuan, koma = desimal -> 1.500,50
        s = s.replace(".", "").replace(",", ".")
    elif has_comma:
        # koma dianggap desimal: "1,5" -> 1.5
        s = s.replace(",", ".")
    elif has_dot:
        # titik: bisa ribuan ("10.000") atau desimal ("1.5")
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            # "10.000" -> ribuan
            s = s.replace(".", "")
        elif all(len(p) == 3 for p in parts[1:]):
            # "1.500.000" -> ribuan
            s = s.replace(".", "")
        # selain itu biarkan sebagai desimal "1.5"
    return float(s)


# angka dalam bentuk kata -> nilai. Berguna untuk input VOICE, mis. hasil
# speech-to-text "sepuluh ribu" / "dua juta lima ratus ribu".
_WORD_UNITS = {
    "nol": 0, "kosong": 0,
    "se": 1, "satu": 1,
    "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9,
    "sepuluh": 10, "sebelas": 11,
}
# kata skala; "ratus/ribu/juta" bisa berdiri sendiri (seratus, seribu)
_WORD_SCALE = {"puluh": 10, "belas": 10, "ratus": 100, "ribu": 1000,
               "rb": 1000, "juta": 1_000_000, "jt": 1_000_000,
               "miliar": 1_000_000_000, "milyar": 1_000_000_000}

_NUM_WORDS = set(_WORD_UNITS) | set(_WORD_SCALE) | {"ratus", "ribu", "juta"}


def _words_to_number(tokens: list[str]) -> int:
    """Konversi deretan kata angka Indonesia menjadi integer.

    Menangani pola umum:
        "sepuluh ribu"            -> 10000
        "dua ratus lima puluh ribu" -> 250000
        "satu juta"               -> 1000000
        "seratus"                 -> 100
        "lima ratus"              -> 500

    Pendekatan: kumpulkan nilai "di bawah seribu" (current) dengan benar,
    lalu kalikan saat ketemu skala besar (ribu/juta/miliar). Satuan kecil
    (puluh/belas/ratus) hanya mengalikan digit TERAKHIR, bukan akumulasi.
    """
    total = 0        # akumulasi hasil skala besar
    current = 0      # nilai < 1000 yang sedang dirangkai
    last = 0         # digit terakhir yang belum dikalikan puluh/ratus

    for w in tokens:
        if w in _WORD_UNITS:
            last = _WORD_UNITS[w]
            current += last
        elif w == "puluh":
            # ubah digit terakhir jadi puluhan: "... lima puluh" -> +50 (ganti 5)
            current = current - last + (last or 1) * 10
            last = 0
        elif w == "belas":
            # "belas" artinya +10 pada digit terakhir: "lima belas" -> 15
            current += 10
            last = 0
        elif w == "ratus":
            current = current - last + (last or 1) * 100
            last = 0
        elif w in ("ribu", "rb"):
            total += (current or 1) * 1000
            current = last = 0
        elif w in ("juta", "jt"):
            total += (current or 1) * 1_000_000
            current = last = 0
        elif w in ("miliar", "milyar"):
            total += (current or 1) * 1_000_000_000
            current = last = 0
    return total + current


# kata satuan-dasar yang menandai "ini angka dalam kata" (bukan digit+unit)
_SPOKEN_BASE = set(_WORD_UNITS) | {"puluh", "belas", "ratus"}


def normalize_spoken_numbers(text: str) -> str:
    """Ganti angka-dalam-kata pada teks menjadi digit.

    Contoh: "beli kopi sepuluh ribu" -> "beli kopi 10000".

    Penting: urutan yang mengandung DIGIT (mis. "10 ribu", "2 juta") TIDAK
    diubah di sini — itu ditangani langsung oleh regex di extract_amount.
    Hanya deretan murni kata-angka yang dikonversi, dan hanya jika ada minimal
    satu kata satuan dasar (se/dua/.../sepuluh/puluh/ratus) supaya kata "ribu"
    atau "juta" yang berdiri sendiri setelah digit tidak salah terkonversi.
    """
    t = text.lower()
    t = re.sub(r"\bseratus\b", "se ratus", t)
    t = re.sub(r"\bseribu\b", "se ribu", t)
    t = re.sub(r"\bsejuta\b", "se juta", t)

    tokens = t.split()
    out: list[str] = []
    buffer: list[str] = []

    def flush():
        if not buffer:
            return
        # hanya konversi bila buffer memuat kata-angka dasar (bukan hanya skala)
        has_base = any(w in _SPOKEN_BASE for w in buffer)
        val = _words_to_number(buffer) if has_base else 0
        if has_base and val:
            out.append(str(val))
        else:
            out.extend(buffer)
        buffer.clear()

    for tok in tokens:
        # kalau token adalah digit, selesaikan buffer kata & biarkan digit apa adanya
        if re.fullmatch(r"\d[\d.,]*", tok):
            flush()
            out.append(tok)
        elif tok in _NUM_WORDS:
            buffer.append(tok)
        else:
            flush()
            out.append(tok)
    flush()
    return " ".join(out)


def extract_amount(text: str) -> int | None:
    """Kembalikan nominal (dalam rupiah, int) pertama yang ditemukan, atau None."""
    # ubah angka-dalam-kata (input voice) jadi digit dulu
    t = normalize_spoken_numbers(text.lower())

    # 1) angka + satuan (ribu/juta/miliar), termasuk singkatan rb/jt/k
    unit_pattern = re.compile(
        r"(?:rp\.?\s*)?(\d+(?:[.,]\d+)*)\s*(miliar|milyar|juta|jt|ribu|rb|k)\b"
    )
    m = unit_pattern.search(t)
    if m:
        value = _to_float(m.group(1))
        unit = m.group(2)
        for pattern, mult in _UNIT_MULTIPLIER:
            if re.fullmatch(pattern, unit):
                return int(round(value * mult))

    # 2) angka polos dengan prefix Rp atau pemisah ribuan
    plain_pattern = re.compile(r"(?:rp\.?\s*)(\d[\d.,]*)")
    m = plain_pattern.search(t)
    if m:
        return int(round(_to_float(m.group(1))))

    # 3) angka polos berukuran "uang" (>= 100) tanpa satuan
    for m in re.finditer(r"\b(\d[\d.,]*\d|\d)\b", t):
        raw = m.group(1)
        # abaikan angka yang jelas bagian nama/satuan (mis. "a4", "ktp") -
        # diatasi oleh \b boundary; di sini cukup filter nilai kecil.
        try:
            val = _to_float(raw)
        except ValueError:
            continue
        if val >= 100:
            return int(round(val))

    return None


if __name__ == "__main__":
    samples = [
        "aku beli kopi 10 ribu",
        "bayar listrik 150rb",
        "liburan 2 juta",
        "bayar sewa 1,5 juta",
        "checkout tokopedia 250 ribu",
        "beli token pln 50000",
        "bayar admin 6500",
        "naik transjakarta 3500",
        "Rp10.000 buat parkir",
        "gaji masuk 5.5 juta",
        "beli kertas a4 55 ribu",
        "beli kopi sepuluh ribu",
        "dapat gaji lima juta",
        "bayar parkir dua ribu",
        "belanja dua ratus lima puluh ribu",
        "transfer seratus ribu",
    ]
    for s in samples:
        print(f"{s!r:45} -> {extract_amount(s)}")