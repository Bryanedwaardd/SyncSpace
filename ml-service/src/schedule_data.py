"""Data intent 'jadwal' + data uji tulisan tangan.

TRAIN dibangkitkan dari template (sintetis) -> variasi terbatas.
TEST ditulis tangan & TIDAK dipakai melatih, supaya skor tidak menipu.
"""
import random

EVENTS = [
    "rapat tim", "rapat himpunan", "kuliah machine learning", "kuliah jarkom", "kerja kelompok",
    "seminar proposal", "praktikum database", "bimbingan skripsi", "ujian algoritma",
    "kuis statistika", "presentasi software engineering", "kumpul bem", "interview magang",
    "latihan futsal", "sidang tugas akhir", "briefing panitia", "asistensi lab", "webinar karir",
    "meeting sama dosen pembimbing", "diskusi proyek", "workshop python", "senam pagi",
    "jadwal dokter gigi", "les bahasa inggris", "kajian rutin", "rapat divisi acara",
]
DATES = ["tanggal 8", "tanggal 12", "tgl 25", "tanggal 3 desember", "besok", "lusa", "hari senin",
         "hari jumat", "hari ini", "kamis depan", "15 desember", "tanggal 20", "tanggal 30 november"]
TIMES = ["jam 8", "jam 8 sampai 10", "jam 10 pagi", "jam 7 malam", "pukul 13.30", "jam 2 siang",
         "jam 9 sampai jam 11", "jam 4 sore", "pukul 19.00-21.00", "jam 8 pagi sampai 12 siang",
         "jam setengah 8", "jam 1 siang sampai 3", "jam delapan sampai sepuluh", "jam tiga sore"]
LEAD = ["ada {e}", "{e}", "ada acara {e}", "jadwal {e}", "ingetin ada {e}", "catat {e}",
        "ada {e} nih", "agenda {e}", "ada {e} ya"]


def make_jadwal_train(n: int = 220, seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    out = set()
    while len(out) < n:
        e = rng.choice(EVENTS)
        lead = rng.choice(LEAD).format(e=e)
        parts = [rng.choice(DATES)] if rng.random() < 0.85 else []
        parts.append(rng.choice(TIMES)) if rng.random() < 0.9 else None
        if not parts:
            parts = [rng.choice(DATES)]
        order = rng.random()
        s = " ".join(parts + [lead]) if order < 0.7 else " ".join([lead] + parts)
        out.add(s)
    return sorted(out)


# ---- DATA UJI TULISAN TANGAN (tidak ikut training) ----
TEST_JADWAL = [
    "tanggal 8 jam 8 sampai 10 ada rapat tim",
    "besok jam 9 ada kuliah pengantar bisnis",
    "kamis jam 3 sore sidang kelompok",
    "ntar jam 7 malem ada ngumpul angkatan",
    "tgl 14 pukul 10.00 sampai 12.00 ujian tengah semester",
    "ada kerja kelompok jumat jam 4 di perpus",
    "lusa jam delapan pagi interview",
    "jadwalin meeting sama klien senin depan jam 2 siang",
    "tanggal 20 desember jam 19.00 acara malam keakraban",
    "hari rabu jam 1 siang konsultasi dosen wali",
    "besok ada praktikum jam 8",
    "sabtu jam 6 pagi lari bareng anak kos",
    "tanggal dua puluh lima jam sembilan sampai sebelas workshop ui ux",
    "minggu depan hari selasa jam 10 rapat proker",
    "jam 5 sore nanti ada latihan band",
]
TEST_NON_JADWAL = [   # termasuk kasus sulit: ada tanggal/jam tapi ini transaksi
    "aku beli kopi 10 ribu",
    "tanggal 25 bayar listrik 150rb",
    "tadi jam 7 malam makan nasi goreng 20 ribu",
    "besok bayar ukt 5 juta",
    "gajian tanggal 1 sebesar 3 juta",
    "kemarin jam 3 sore isi bensin 30rb",
    "dapat uang saku dari ortu 1 juta",
    "jual buku bekas 40 ribu",
    "bayar kos tanggal 5 sebesar 800 ribu",
    "nonton bioskop jam 7 malam 50rb",
    "transfer ke temen 100 ribu",
    "beli tiket kereta 250 ribu",
    "terima bonus freelance 500 ribu",
    "makan siang di kantin 15 ribu",
    "bayar parkir 2 ribu",
]

# ---- KASUS SULIT (tulisan tangan, tidak ikut training) ----
# jadwal TANPA ekspresi waktu eksplisit, atau waktu pakai kata yang belum didukung
HARD_JADWAL = [
    "ada rapat himpunan",
    "nanti malam ada kumpul angkatan",
    "ada seminar karir di aula kampus",
    "jangan lupa kerja kelompok ML",
    "ntar sore latihan futsal",
    "besok ada ujian algoritma",
]
# transaksi yang tidak punya nominal / mirip jadwal
HARD_UANG = [
    "bayar kos",
    "makan malam sama temen",
    "beli tiket seminar 75 ribu",
    "bayar iuran rapat himpunan 20rb",
    "ikut workshop python bayar 100 ribu",
    "dikasih ortu buat kuliah",
]