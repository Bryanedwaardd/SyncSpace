"""
Parser waktu & tanggal Bahasa Indonesia (rule-based) untuk input jadwal.

Contoh:
    "tanggal 8 jam 8 sampai 10 ada rapat tim"
    -> date=2026-12-08, start=08:00, end=10:00, title="Rapat tim"

Kenapa rule-based? Pola waktu ("jam 8", "besok", "tanggal 8") sangat teratur,
jadi aturan lebih akurat, bisa dijelaskan, dan tidak butuh data latih.
ML dipakai untuk bagian yang AMBIGU (apakah kalimat ini jadwal atau transaksi).
"""
import re
from datetime import date, timedelta

try:
    from .amount_parser import normalize_spoken_numbers
except ImportError:
    from amount_parser import normalize_spoken_numbers

MONTHS = {
    "januari": 1, "jan": 1, "februari": 2, "feb": 2, "maret": 3, "mar": 3,
    "april": 4, "apr": 4, "mei": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "agt": 8, "september": 9, "sep": 9,
    "oktober": 10, "okt": 10, "november": 11, "nov": 11, "desember": 12, "des": 12,
}
WEEKDAYS = {"senin": 0, "selasa": 1, "rabu": 2, "kamis": 3, "jumat": 4,
            "jum'at": 4, "sabtu": 5, "minggu": 6, "ahad": 6}

_MON = "|".join(sorted(MONTHS, key=len, reverse=True))
_PERIOD = r"(pagi|siang|sore|malam|subuh)"
_H = r"(\d{1,2})(?:[.:](\d{2}))?"
_SEP = r"(?:-|–|sampai|sampe|smpe|s/d|hingga|until)"

# jam 8 [pagi] sampai [jam] 10 [malam]   (rentang)
_RANGE = re.compile(
    rf"(?:jam|pukul|pkl)\s*{_H}\s*{_PERIOD}?\s*{_SEP}\s*(?:jam|pukul|pkl)?\s*{_H}\s*{_PERIOD}?\b"
)
# jam setengah 8  (= 07:30)
_HALF = re.compile(rf"(?:jam|pukul|pkl)\s*setengah\s*(\d{{1,2}})\s*{_PERIOD}?\b")
# jam 8 [pagi]   (tunggal)
_SINGLE = re.compile(rf"(?:jam|pukul|pkl)\s*{_H}\s*{_PERIOD}?\b")

_DATE_TGL = re.compile(rf"\b(?:tanggal|tgl)\s*(\d{{1,2}})(?:\s*({_MON})\b(?:\s*(\d{{4}}))?)?")
_DATE_DMY = re.compile(rf"\b(\d{{1,2}})\s*({_MON})\b(?:\s*(\d{{4}}))?")
_DATE_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_DATE_REL = re.compile(r"\b(hari ini|besok|lusa)\b")
_DATE_DAY = re.compile(
    r"\b(?:hari\s+)?(senin|selasa|rabu|kamis|jumat|jum'at|sabtu|ahad)(?:\s+(depan|ini))?\b"
    r"|\bhari\s+(minggu)(?:\s+(depan|ini))?\b"
)

_FILLER = {"ada", "ya", "nih", "dong", "deh", "tolong", "catat", "catatin",
           "jadwalkan", "jadwal", "agenda", "tambahin", "tambah", "buat", "buatin",
           "acara", "kegiatan", "yaa", "yah", "nanti", "ingetin", "ingatkan",
           "ke", "pada", "untuk", "di", "dan"}


def _hhmm(h: int, m: int = 0) -> str:
    return f"{h % 24:02d}:{m:02d}"


def _resolve_hour(h: int, period: str | None) -> tuple[int, bool]:
    """Ubah jam 12-jam ke 24-jam. Return (jam24, ditebak?)."""
    if h >= 13:
        return h, False
    if period in ("pagi", "subuh"):
        return (0 if h == 12 else h), False
    if period == "siang":
        return (h if h >= 11 else h + 12), False
    if period == "sore":
        return (h + 12 if h < 12 else h), False
    if period == "malam":
        if h == 12:
            return 0, False
        return (h + 12 if h >= 5 else h), False
    # tanpa penanda: 7-11 dianggap pagi, 12 siang (cukup yakin);
    # 1-6 dianggap sore/malam TAPI ditandai "ditebak" -> minta konfirmasi
    if h == 12 or h >= 7:
        return h, False
    return h + 12, True


def parse_time(text: str):
    """Cari jam mulai/selesai. Return (start, end, assumed, span) atau None."""
    m = _RANGE.search(text)
    if m:
        h1, m1, p1, h2, m2, p2 = m.groups()
        h1, h2 = int(h1), int(h2)
        m1, m2 = int(m1 or 0), int(m2 or 0)
        end_h, a2 = _resolve_hour(h2, p2)
        if p1 is None and p2 in ("sore", "malam"):
            p1 = p2                       # "jam 8 sampai 10 malam" -> keduanya malam
        start_h, a1 = _resolve_hour(h1, p1)
        if start_h * 60 + m1 >= end_h * 60 + m2:
            # mis. "jam 11 sampai 1" -> 11:00-13:00
            if end_h < 12:
                end_h += 12
            if start_h * 60 + m1 >= end_h * 60 + m2 and start_h >= 12:
                start_h -= 12
        return _hhmm(start_h, m1), _hhmm(end_h, m2), (a1 or a2), m.span()

    m = _HALF.search(text)
    if m:
        h, p = int(m.group(1)), m.group(2)
        hh, a = _resolve_hour(h, p)
        hh -= 1
        return _hhmm(hh, 30), None, a, m.span()

    m = _SINGLE.search(text)
    if m:
        h, mi, p = int(m.group(1)), int(m.group(2) or 0), m.group(3)
        hh, a = _resolve_hour(h, p)
        return _hhmm(hh, mi), None, a, m.span()
    return None


def parse_date(text: str, today: date):
    """Cari tanggal. Return (date|None, ditebak_bulan?, span) atau None bila tak ada."""
    m = _DATE_TGL.search(text) or _DATE_DMY.search(text)
    if m:
        day = int(m.group(1))
        mon = MONTHS.get(m.group(2)) if m.group(2) else None
        yr = int(m.group(3)) if m.group(3) else None
        guessed = False
        if mon is None:                         # "tanggal 8" tanpa bulan
            mon, yr = today.month, today.year
            if day < today.day:                 # sudah lewat -> bulan depan
                mon += 1
                if mon == 13:
                    mon, yr = 1, yr + 1
            guessed = True
        elif yr is None:
            yr = today.year
            if date_safe(yr, mon, day) and date_safe(yr, mon, day) < today:
                yr += 1
        return date_safe(yr, mon, day), guessed, m.span()

    m = _DATE_SLASH.search(text)
    if m:
        day, mon = int(m.group(1)), int(m.group(2))
        yr = int(m.group(3)) if m.group(3) else today.year
        if yr < 100:
            yr += 2000
        return date_safe(yr, mon, day), False, m.span()

    m = _DATE_REL.search(text)
    if m:
        off = {"hari ini": 0, "besok": 1, "lusa": 2}[m.group(1)]
        return today + timedelta(days=off), False, m.span()

    m = _DATE_DAY.search(text)
    if m:
        name = m.group(1) or m.group(3)
        mod = m.group(2) or m.group(4)
        ahead = (WEEKDAYS[name] - today.weekday()) % 7
        if mod == "depan" and ahead == 0:
            ahead = 7
        return today + timedelta(days=ahead), False, m.span()
    return None


def date_safe(y: int, mo: int, d: int):
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def mask_time(text: str) -> str:
    """Ganti ekspresi waktu/tanggal dengan token. Dipakai sebelum klasifikasi intent
    supaya model belajar dari "ada ekspresi waktu", bukan dari angka spesifik."""
    t = normalize_spoken_numbers(text)
    for pat, tok in ((_RANGE, " tokwaktu "), (_HALF, " tokwaktu "), (_SINGLE, " tokwaktu "),
                     (_DATE_TGL, " tokdate "), (_DATE_DMY, " tokdate "),
                     (_DATE_SLASH, " tokdate "), (_DATE_REL, " tokdate "),
                     (_DATE_DAY, " tokdate ")):
        t = pat.sub(tok, t)
    return t


def parse_schedule(text: str, today: date | None = None) -> dict:
    """Teks -> draf agenda. Tidak menebak diam-diam: field yang kurang/ditebak
    dicatat di `missing` / `assumptions` dan needs_confirmation=True."""
    today = today or date.today()
    t = normalize_spoken_numbers(text)       # lowercase + "delapan" -> "8"

    tm = parse_time(t)
    spans = []
    start = end = None
    assumptions, missing = [], []
    if tm:
        start, end, assumed, sp = tm
        spans.append(sp)
        if assumed:
            assumptions.append("am_pm_ditebak")
    # buang span jam dulu agar angkanya tidak terbaca sebagai tanggal
    t_no_time = t
    for a, b in spans:
        t_no_time = t_no_time[:a] + " " * (b - a) + t_no_time[b:]

    dt = parse_date(t_no_time, today)
    ev_date = None
    if dt:
        ev_date, guessed, sp = dt
        spans.append(sp)
        if guessed:
            assumptions.append("bulan_ditebak")
        if ev_date is None:
            missing.append("date")           # mis. tanggal 31 Februari
    else:
        missing.append("date")
    if start is None:
        missing.append("start_time")

    rest = t_no_time
    if dt:
        a, b = dt[2]
        rest = rest[:a] + " " * (b - a) + rest[b:]
    words = [w for w in re.findall(r"[a-z0-9&']+", rest) if w not in {"jam", "pukul"}]
    while words and words[0] in _FILLER:
        words.pop(0)
    while words and words[-1] in _FILLER:
        words.pop()
    title = " ".join(words).capitalize() or None
    if title is None:
        missing.append("title")

    return {
        "title": title,
        "date": ev_date.isoformat() if ev_date else None,
        "start_time": start,
        "end_time": end,
        "missing": missing,
        "assumptions": assumptions,
        # bulan_ditebak hanya info; jam am/pm ditebak atau field kurang -> konfirmasi
        "needs_confirmation": bool(missing or "am_pm_ditebak" in assumptions),
    }


if __name__ == "__main__":
    import json
    ref = date(2026, 11, 18)   # Rabu
    for s in [
        "tanggal 8 jam 8 sampai 10 ada rapat tim",
        "besok jam 7 malam kerja kelompok ML",
        "jam delapan sampai sepuluh pagi kuliah jarkom hari senin",
        "tanggal lima belas desember pukul 13.30-15.00 seminar proposal",
        "lusa jam setengah 8 praktikum database",
        "tanggal 31 februari jam 9 rapat",
        "ada rapat himpunan",
    ]:
        print(s, "\n  ", json.dumps(parse_schedule(s, ref), ensure_ascii=False))