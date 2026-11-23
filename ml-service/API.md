# ML Service API

Layanan NLP untuk memahami teks, suara, dan foto struk menjadi data transaksi atau agenda.
Dibangun dengan FastAPI. Tanpa LLM: TF-IDF + Logistic Regression + aturan (regex).

## Menjalankan

Dari folder `ml-service`:

```powershell
pip install -r requirements.txt
python src/train.py
python src/train_intent.py
python -m uvicorn api:app --app-dir src --port 8000
```

- File model (`.joblib`) **tidak ikut repo**, jadi dua perintah `train` wajib dijalankan sekali sebelum server dinyalakan.
- Server hidup di `http://127.0.0.1:8000`. Dokumentasi interaktif: `http://127.0.0.1:8000/docs`.
- Pertama kali endpoint suara atau gambar dipanggil, model Whisper dan EasyOCR diunduh (ratusan MB), jadi request pertama lambat.
  Atur timeout minimal 60 detik untuk `/parse/voice` dan `/parse/image`.

## Endpoint

| Method | Path | Input | Keterangan |
|---|---|---|---|
| POST | `/api/v1/parse/text` | JSON `{"text": "..."}` | teks bebas, otomatis dideteksi transaksi atau jadwal |
| POST | `/api/v1/parse/voice` | `multipart/form-data`, field `file` | audio (wav/mp3/m4a/ogg) lalu Whisper lalu seperti teks |
| POST | `/api/v1/parse/image` | `multipart/form-data`, field `file` | foto struk (jpg/png) lalu OCR lalu kategori dan total |
| GET | `/health` | - | cek server hidup |

## Format respons

Ketiga endpoint parse mengembalikan JSON dengan **enam kunci yang selalu ada**:

```json
{
  "intent": "EXPENSE",
  "category": "Food & Beverage",
  "amount": 25000,
  "extracted_text": "Beli kopi 25rb",
  "needs_confirmation": false,
  "event": null
}
```

| Kunci | Tipe | Arti |
|---|---|---|
| `intent` | string | `EXPENSE`, `INCOME`, atau `SCHEDULE` |
| `category` | string atau null | kategori (tabel di bawah). `null` bila `SCHEDULE` |
| `amount` | integer atau null | nominal dalam rupiah. `null` bila tidak ditemukan atau `SCHEDULE`. Untuk struk, ini total belanja |
| `extracted_text` | string | teks yang dibaca sistem: teks input, hasil transkrip suara, atau hasil OCR struk |
| `needs_confirmation` | boolean | `true` berarti aplikasi **harus meminta konfirmasi user** sebelum menyimpan |
| `event` | object atau null | isi agenda bila `intent` = `SCHEDULE`, selain itu `null` |

### Kapan `needs_confirmation` bernilai true

Sistem tidak boleh asal menebak. Nilainya `true` bila:

- transaksi: nominal tidak ditemukan, atau keyakinan model rendah;
- jadwal: tanggal, jam mulai, atau judul tidak ada, atau jam AM/PM ditebak;
- struk: total tidak terbaca, atau kategori ditebak classifier (bukan dari nama toko atau kata kunci).

### Objek `event` (hanya untuk SCHEDULE)

```json
{
  "title": "Kerja kelompok ml",
  "date": "2026-11-21",
  "start_time": "19:00",
  "end_time": null,
  "missing": [],
  "assumptions": [],
  "needs_confirmation": false
}
```

`date` berformat `YYYY-MM-DD`, jam berformat `HH:MM` (24 jam). `missing` berisi nama field yang tidak ditemukan
(`date`, `start_time`, `title`). `assumptions` berisi tebakan sistem (`am_pm_ditebak`, `bulan_ditebak`).

## Kategori

Pengeluaran (`EXPENSE`):

| Label ML | Dikirim ke backend |
|---|---|
| Makanan & Minuman | Food & Beverage |
| Transport | Transportation |
| Belanja | Shopping |
| Tagihan | Bills |
| Hiburan | Entertainment |
| Pendidikan | Education |
| Lainnya | Others |

Pemasukan (`INCOME`): Gaji = `Salary`, Bonus = `Bonus`, Penjualan = `Sales`, Transfer Masuk = `Transfer In`, Lainnya = `Others`.

Terjemahan ini ada di satu tabel di `src/contract.py`. Kalau istilahnya perlu diganti, ubah di sana (tidak perlu melatih ulang model).

## Contoh pemanggilan

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/parse/text `
  -ContentType "application/json" -Body '{"text": "Beli kopi 25rb"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/parse/text \
  -H "Content-Type: application/json" -d '{"text": "Beli kopi 25rb"}'

curl -X POST http://127.0.0.1:8000/api/v1/parse/image -F "file=@struk.jpg"
```

## Error

| Status | Penyebab |
|---|---|
| 422 | audio tanpa ucapan terdeteksi, gambar tanpa teks terbaca, atau body JSON tidak valid |

## Privasi

Audio dan foto struk adalah data pribadi. Server hanya menyimpannya sebagai file sementara selama diproses,
lalu langsung menghapusnya. Backend sebaiknya tidak menyimpan file mentah lebih lama dari yang perlu.

## Batasan yang perlu diketahui

- Whisper dan EasyOCR adalah model pretrained, akurasinya turun pada audio berisik, aksen kuat, atau struk pudar dan miring.
- Arah transaksi kadang ambigu ("bayar utang ke temen" vs "temen bayar utang").
- Kategori yang tumpang tindih (nongkrong di kafe, beli laptop untuk kuliah) bisa salah. Itu sebabnya ada `needs_confirmation`.
