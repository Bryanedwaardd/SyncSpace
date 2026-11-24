# Money Tracking NLP (Bahasa Indonesia)

Model NLP untuk mengubah kalimat natural (teks **atau voice**) menjadi data
transaksi terstruktur. Contoh: `"aku beli kopi 10 ribu"` menjadi:

```json
{
  "text": "aku beli kopi 10 ribu",
  "type": "pengeluaran",
  "category": "Makanan & Minuman",
  "amount": 10000,
  "item": "kopi",
  "confidence": { "type": 0.95, "category": 0.80 }
}
```

## Yang bisa dilakukan sekarang

1. **Membedakan jenis transaksi** — `pemasukan` vs `pengeluaran`
   (mis. "dapat gaji 5 juta" = pemasukan, "beli kopi 10 ribu" = pengeluaran).
2. **Klasifikasi kategori**:
   - Pengeluaran: `Makanan & Minuman`, `Transport`, `Tagihan`, `Belanja`, `Hiburan`, `Pendidikan`, `Lainnya`
   - Pemasukan: `Gaji`, `Bonus`, `Transfer Masuk`, `Penjualan`, `Lainnya`
3. **Ekstraksi nominal** — "10 ribu", "10rb", "1,5 juta", "Rp10.000", "50000" dst.
4. **Ekstraksi item** sederhana (kata kunci barang/kegiatan).
5. **Input voice** — ucapkan transaksinya, audio diubah ke teks (Whisper offline)
   lalu diproses sama seperti input teks. Mis. voice "beli kopi 10 ribu" tetap
   masuk ke `pengeluaran / Makanan & Minuman / 10000`.
6. **Input gambar struk** — foto struk belanja dibaca OCR (EasyOCR offline),
   lalu diambil **kategori** (dari nama toko/merchant) + **total** belanja.
   Mis. struk Indomaret -> `pengeluaran / Belanja / total 17000`.

## Struktur folder

```
Project ML/
├── data/
│   └── transactions.csv      # dataset latih (text, type, category)
├── models/                   # hasil training (dibuat otomatis)
│   ├── type_model.joblib
│   └── category_model.joblib
├── src/
│   ├── amount_parser.py      # ekstraksi nominal (rule-based)
│   ├── train.py              # training 2 classifier TF-IDF + LogisticRegression
│   ├── predict.py            # TransactionParser: gabungan model + parser (dipakai backend)
│   ├── speech.py             # speech-to-text (voice -> teks) pakai faster-whisper
│   ├── ocr.py                # OCR gambar struk (gambar -> teks) pakai EasyOCR
│   ├── receipt_parser.py     # ReceiptParser: teks struk -> {kategori, total}
│   ├── download_model.py     # unduh model whisper dgn resume + retry (koneksi lambat)
│   └── api.py                # REST API: /parse, /parse-voice, /parse-receipt
├── test_voice.py             # uji cepat: audio -> teks -> transaksi
├── test_ocr.py               # uji cepat: gambar struk -> {kategori, total}
├── sample_voice.wav          # contoh audio untuk tes
├── sample_receipt.png        # contoh gambar struk untuk tes
├── requirements.txt
└── README.md
```

## Arsitektur

Pendekatan **hybrid**:

| Komponen        | Metode                                   | Alasan                                               |
| --------------- | ---------------------------------------- | ---------------------------------------------------- |
| type & category | ML (TF-IDF n-gram + LogisticRegression)  | Memahami variasi bahasa & typo ringan                |
| amount (nominal)| Rule-based regex                         | Angka lebih andal & deterministik dengan aturan      |
| item            | Rule-based (hapus stopword + kata kerja) | Cukup untuk label singkat tanpa butuh model terpisah |
| voice           | Whisper (faster-whisper) offline di CPU  | Akurat untuk Bahasa Indonesia, tanpa internet/API key|
| struk (OCR)     | EasyOCR offline + kata kunci merchant    | Baca total & tebak kategori dari nama toko           |

Saat training, nominal dibuang dari teks (`clean_text`) agar model fokus pada
kata kunci, bukan pada angka.

## Cara pakai

Install dependency:

```bash
pip install -r requirements.txt
```

Latih model (menghasilkan file di `models/`):

```bash
python src/train.py
```

Uji prediksi dari command line:

```bash
python src/predict.py
```

### Dipakai dari backend (Python)

```python
from predict import TransactionParser

parser = TransactionParser()           # load model sekali di startup
hasil = parser.parse("aku beli kopi 10 ribu")
```

### Dipakai sebagai REST API

```bash
python -m uvicorn src.api:app --reload
```

Lalu kirim request:

```bash
POST http://127.0.0.1:8000/parse
{ "text": "aku beli kopi 10 ribu" }
```

### Input VOICE (speech-to-text)

Kirim file audio (wav/mp3/m4a/ogg) sebagai `multipart/form-data` dengan field
bernama `file`:

```bash
POST http://127.0.0.1:8000/parse-voice
form-data:  file = rekaman.wav
```

Responnya sama persis dengan `/parse` — audio diubah jadi teks lalu diproses.

Catatan model Whisper:

- Default model `small` (~480MB) sudah terunduh ke cache lokal
  (`~/.cache/huggingface`). Jalan offline di CPU (int8), tanpa GPU/internet/API key.
  Model `small` dipilih karena `tiny` sering salah transkripsi Bahasa Indonesia.
- Ukuran model bisa diatur lewat env var `MONEYNLP_WHISPER_MODEL`
  (`tiny` / `base` / `small` / `medium`). Model lebih besar = lebih akurat tapi
  lebih lambat & butuh RAM lebih.
  Contoh (PowerShell): `$env:MONEYNLP_WHISPER_MODEL="base"` sebelum start server.
- **Kecepatan:** di CPU, load + inference model `small` makan beberapa menit pada
  pemanggilan PERTAMA. Lewat API, model di-load sekali saat server start, lalu
  request `/parse-voice` berikutnya jauh lebih cepat (model sudah di memori).
- Kalau perlu unduh ukuran lain dan koneksi ke Hugging Face sering putus,
  pakai skrip resume berikut:

  ```bash
  python src/download_model.py base      # unduh dgn resume + retry otomatis
  ```

### Uji cepat voice dari command line

Sudah disediakan `test_voice.py` + contoh audio `sample_voice.wav`:

```bash
python test_voice.py                 # pakai sample_voice.wav
python test_voice.py rekamanku.wav   # pakai file audiomu sendiri
```

### Catatan akurasi voice

- Nominal yang diucapkan sebagai kata ("sepuluh ribu", "dua ratus lima puluh
  ribu", "lima juta") otomatis dikonversi ke angka oleh `amount_parser`.
- Akurasi transkripsi sangat bergantung pada kualitas audio dan ukuran model.
  Model `tiny` cukup untuk uji coba; untuk produksi gunakan `small` atau `base`
  agar ucapan angka lebih akurat. Rekaman suara manusia asli jauh lebih baik
  dibanding audio sintetis (text-to-speech).

### Input GAMBAR STRUK (OCR)

Kirim gambar struk (jpg/png) sebagai `multipart/form-data` dengan field `file`:

```bash
POST http://127.0.0.1:8000/parse-receipt
form-data:  file = struk.jpg
```

Respon berisi kategori + total (tanpa rincian item):

```json
{
  "type": "pengeluaran",
  "category": "Belanja",
  "total": 17000,
  "category_method": "keyword"
}
```

Uji cepat dari command line (ada contoh `sample_receipt.png`):

```bash
python test_ocr.py                 # pakai sample_receipt.png
python test_ocr.py struk_saya.jpg  # pakai foto struk sendiri
```

Cara kerja:

- **Total** diambil dari baris bertuliskan "TOTAL" (menghindari "subtotal" &
  "tunai/kembali"); kalau tidak ketemu, pakai angka uang terbesar di struk.
- **Kategori** ditebak dari nama toko/merchant (mis. Indomaret -> Belanja,
  Starbucks -> Makanan & Minuman, Pertamina -> Transport). Kalau merchant tak
  dikenali, dipakai classifier NLP atas teks struk (`category_method: "model"`).
- Model EasyOCR (~64MB) terunduh otomatis sekali saat pertama dipakai, lalu
  di-cache. Jalan offline di CPU. Seperti voice, OCR pertama agak lambat; lewat
  API reader di-load sekali saat server start.
- Daftar merchant bisa ditambah di `src/receipt_parser.py`
  (`_STRONG_MERCHANTS` & `_MERCHANT_KEYWORDS`).

## Catatan & langkah lanjut

- Dataset saat ini ~300 baris. Akurasi pembeda `pemasukan`/`pengeluaran` sudah
  tinggi (~93%). Akurasi kategori masih bisa naik dengan menambah contoh,
  terutama kategori yang datanya sedikit (`Bonus`, `Transfer Masuk`).
- Untuk meningkatkan model: tambah baris ke `data/transactions.csv` lalu jalankan
  `python src/train.py` lagi. Tidak perlu ubah kode.
- Tahap berikutnya yang bisa dikembangkan: deteksi tanggal/waktu ("kemarin",
  "tadi pagi"), multi-transaksi dalam satu kalimat, dan asisten pribadi (intent
  selain pencatatan, mis. "berapa pengeluaran makan minggu ini").
```
