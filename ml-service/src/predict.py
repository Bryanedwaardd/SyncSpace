"""
Modul prediksi untuk backend money tracking.

Menggabungkan:
  - type_model     : pemasukan / pengeluaran
  - category_model : kategori transaksi
  - amount_parser  : ekstraksi nominal (rule-based)
  - ekstraksi item sederhana dari teks

Contoh pemakaian dari backend:

    from predict import TransactionParser

    parser = TransactionParser()          # load model sekali saat startup
    result = parser.parse("aku beli kopi 10 ribu")
    # {
    #   "text": "aku beli kopi 10 ribu",
    #   "type": "pengeluaran",
    #   "category": "Makanan & Minuman",
    #   "amount": 10000,
    #   "item": "kopi",
    #   "confidence": {"type": 0.98, "category": 0.95}
    # }
"""

import re
from pathlib import Path

import joblib

try:
    # saat diimpor sebagai bagian package (mis. uvicorn src.api:app)
    from .amount_parser import _NUM_WORDS, extract_amount, normalize_spoken_numbers
    from .train import clean_text
except ImportError:
    # saat dijalankan langsung dari dalam folder src/
    from amount_parser import _NUM_WORDS, extract_amount, normalize_spoken_numbers
    from train import clean_text

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

# kata yang biasanya bukan "item" (kata kerja / pengisi)
_STOPWORDS = {
    "aku", "saya", "gue", "gua", "ku", "tadi", "barusan", "baru", "udah", "sudah",
    "beli", "bayar", "byr", "beliin", "belanja", "isi", "pesan", "pesen", "makan",
    "mkn", "minum", "naik", "dapat", "dapet", "terima", "kirim", "kirimin", "transfer",
    "buat", "untuk", "di", "ke", "dari", "yang", "sama", "dengan", "habis", "senilai",
    "sebesar", "seharga", "an", "nya", "ini", "itu", "bulan", "hari", "online",
    "top", "up", "checkout", "jual", "dikasih", "dikirimin", "dibayar", "menang",
    "perpanjang", "langganan", "pakai", "pake",
}


class TransactionParser:
    def __init__(self, model_dir: Path = MODEL_DIR):
        type_path = model_dir / "type_model.joblib"
        category_path = model_dir / "category_model.joblib"
        if not type_path.exists() or not category_path.exists():
            raise FileNotFoundError(
                f"Model belum ada di {model_dir}. Jalankan 'python src/train.py' dulu."
            )
        self.type_model = joblib.load(type_path)
        self.category_model = joblib.load(category_path)

    def _predict_with_conf(self, model, text: str):
        label = model.predict([text])[0]
        conf = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba([text])[0]
            conf = round(float(max(proba)), 4)
        return label, conf

    def _extract_item(self, raw_text: str) -> str | None:
        """Tebak 'item' transaksi: kata benda setelah kata kerja, tanpa angka."""
        # ubah angka-kata jadi digit dulu, lalu clean_text membuang digitnya,
        # supaya "kopi sepuluh ribu" -> item "kopi" (bukan "kopi sepuluh ribu")
        t = clean_text(normalize_spoken_numbers(raw_text))
        tokens = [
            w
            for w in t.split()
            if w not in _STOPWORDS and w not in _NUM_WORDS and len(w) > 1
        ]
        if not tokens:
            return None
        # ambil maksimal 3 kata pertama yang bermakna sebagai item
        return " ".join(tokens[:3])

    def parse(self, text: str) -> dict:
        clean = clean_text(text)
        tipe, type_conf = self._predict_with_conf(self.type_model, clean)
        category, cat_conf = self._predict_with_conf(self.category_model, clean)
        amount = extract_amount(text)
        item = self._extract_item(text)

        return {
            "text": text,
            "type": tipe,
            "category": category,
            "amount": amount,
            "item": item,
            "confidence": {"type": type_conf, "category": cat_conf},
        }


if __name__ == "__main__":
    import json

    parser = TransactionParser()
    tests = [
        "aku beli kopi 10 ribu",
        "makan siang di warteg 15rb",
        "isi bensin 30 ribu",
        "bayar listrik bulan ini 150 ribu",
        "gajian bulan ini 5 juta",
        "dapat uang saku dari orang tua 1 juta",
        "checkout tokopedia beli sepatu 400 ribu",
        "jual hp lama 1 juta",
        "bayar ukt 5 juta",
        "nonton bioskop 50rb",
    ]
    for t in tests:
        print(json.dumps(parser.parse(t), ensure_ascii=False))
