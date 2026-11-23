"""
Lapisan terjemahan: hasil internal ML  ->  format kontrak dengan backend.

Kenapa dipisah? Model dan data latih memakai label Bahasa Indonesia
("pengeluaran", "Makanan & Minuman"). Backend (Spring Boot) mengharapkan
label Inggris huruf besar ("EXPENSE", "Food & Beverage"). Daripada mengubah
data latih dan melatih ulang, kita menerjemahkan di pintu keluar saja.
Kalau PM mengganti istilah, cukup ubah tabel di file ini.

Format keluaran (selalu enam kunci, supaya mudah dibuat DTO di Java):
    {
      "intent": "EXPENSE" | "INCOME" | "SCHEDULE",
      "category": "Food & Beverage" | ... | null,
      "amount": 25000 | null,
      "extracted_text": "Beli kopi 25rb",
      "needs_confirmation": false,
      "event": null | {title, date, start_time, end_time, missing, assumptions}
    }

Empat kunci pertama sesuai permintaan PM. `needs_confirmation` dan `event`
adalah TAMBAHAN (lihat INCLUDE_EXTRAS di bawah).
"""

# ---- Tabel terjemahan (ubah di sini kalau PM mengganti istilah) ----
INTENT_MAP = {
    "pengeluaran": "EXPENSE",
    "pemasukan": "INCOME",
    "jadwal": "SCHEDULE",
}

# "Lainnya" ada di pengeluaran DAN pemasukan, jadi tabelnya dipisah per intent.
CATEGORY_MAP = {
    "EXPENSE": {
        "Makanan & Minuman": "Food & Beverage",
        "Transport": "Transportation",
        "Belanja": "Shopping",
        "Tagihan": "Bills",
        "Hiburan": "Entertainment",
        "Pendidikan": "Education",
        "Lainnya": "Others",
    },
    "INCOME": {
        "Gaji": "Salary",
        "Bonus": "Bonus",
        "Penjualan": "Sales",
        "Transfer Masuk": "Transfer In",
        "Lainnya": "Others",
    },
}

# Pengaman: bila False, field needs_confirmation dan event dibuang dari
# keluaran sehingga persis empat kunci PM. TIDAK disarankan: tanpa
# needs_confirmation, backend tidak tahu kapan harus minta konfirmasi user.
INCLUDE_EXTRAS = True


def _finish(out: dict) -> dict:
    if not INCLUDE_EXTRAS:
        out.pop("needs_confirmation", None)
        out.pop("event", None)
    return out


def translate_category(intent: str, category: str | None) -> str | None:
    """Terjemahkan kategori. Kalau tidak ada di tabel, kembalikan apa adanya
    (lebih baik label Indonesia daripada hilang atau error)."""
    if category is None:
        return None
    return CATEGORY_MAP.get(intent, {}).get(category, category)


def from_assistant(result: dict, extracted_text: str) -> dict:
    """Hasil AssistantParser.parse() (teks / suara) -> format kontrak."""
    intent = INTENT_MAP.get(result.get("type"), "EXPENSE")

    if intent == "SCHEDULE":
        return _finish({
            "intent": intent,
            "category": None,
            "amount": None,
            "extracted_text": extracted_text,
            "needs_confirmation": bool(result.get("needs_confirmation", True)),
            "event": result.get("event"),
        })

    return _finish({
        "intent": intent,
        "category": translate_category(intent, result.get("category")),
        "amount": result.get("amount"),
        "extracted_text": extracted_text,
        "needs_confirmation": bool(result.get("needs_confirmation", False)),
        "event": None,
    })


def from_receipt(result: dict) -> dict:
    """Hasil ReceiptParser.parse() (gambar struk) -> format kontrak.

    Struk selalu pengeluaran. Perlu konfirmasi bila total tidak terbaca, atau
    kategori ditebak classifier (bukan dari nama toko/kata kunci) karena itu
    lebih lemah.
    """
    intent = "EXPENSE"
    total = result.get("total")
    weak_category = result.get("category_method") == "model"
    return _finish({
        "intent": intent,
        "category": translate_category(intent, result.get("category")),
        "amount": total,
        "extracted_text": result.get("raw_text", ""),
        "needs_confirmation": total is None or weak_category,
        "event": None,
    })