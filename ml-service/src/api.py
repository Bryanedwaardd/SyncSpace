"""
Contoh REST API backend untuk money tracking NLP.

Jalankan:
    uvicorn api:app --reload --app-dir src
atau dari folder Project ML:
    python -m uvicorn src.api:app --reload

Endpoint:
    POST /parse        -> parsing dari TEKS
        body: {"text": "aku beli kopi 10 ribu"}

    POST /parse-voice  -> parsing dari VOICE (upload file audio)
        form-data: file=<audio wav/mp3/m4a/ogg>
        proses: audio -> whisper (speech-to-text) -> teks -> parser
        respon sama dgn /parse

    POST /parse-receipt -> parsing dari GAMBAR STRUK (upload gambar)
        form-data: file=<gambar jpg/png>
        proses: gambar -> OCR -> teks struk -> {category, total}
        respon:
            {
                "type": "pengeluaran",
                "category": "Belanja",
                "total": 17000,
                "category_method": "keyword"
            }

    Respon /parse & /parse-voice:
        {
            "text": "aku beli kopi 10 ribu",
            "type": "pengeluaran",
            "category": "Makanan & Minuman",
            "amount": 10000,
            "item": "kopi",
            "confidence": {"type": 0.95, "category": 0.80}
        }

    GET /health -> status model
"""

import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

try:
    from .predict import TransactionParser
    from .receipt_parser import ReceiptParser
    from .router import AssistantParser
except ImportError:
    from predict import TransactionParser
    from receipt_parser import ReceiptParser
    from router import AssistantParser

app = FastAPI(title="Money Tracking NLP API", version="1.3.0")

# load model NLP sekali saat startup (di-cache selama proses hidup)
parser = TransactionParser()
receipt_parser = ReceiptParser()
assistant = AssistantParser()   # router: jadwal vs transaksi


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    text: str
    type: str
    category: str
    amount: int | None
    item: str | None
    confidence: dict


class ReceiptResponse(BaseModel):
    type: str
    category: str
    total: int | None
    category_method: str


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/parse-any")
def parse_any(req: ParseRequest):
    """Teks bebas -> otomatis dideteksi: transaksi ATAU draf agenda (jadwal)."""
    return assistant.parse(req.text)


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest):
    """Parsing transaksi dari teks."""
    return parser.parse(req.text)


@app.post("/parse-voice", response_model=ParseResponse)
async def parse_voice(file: UploadFile = File(...)):
    """Parsing transaksi dari file audio (voice).

    Alur: terima upload audio -> transcribe pakai Whisper -> parse jadi JSON.
    Import speech ditunda ke dalam fungsi agar server tetap bisa start walau
    model whisper belum terunduh.
    """
    try:
        from .speech import transcribe
    except ImportError:
        from speech import transcribe

    # simpan upload ke file sementara (whisper butuh path file)
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        text = transcribe(tmp_path)
        if not text:
            raise HTTPException(
                status_code=422,
                detail="Tidak ada ucapan terdeteksi pada audio.",
            )

        result = parser.parse(text)
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/parse-receipt", response_model=ReceiptResponse)
async def parse_receipt(file: UploadFile = File(...)):
    """Parsing transaksi dari gambar struk.

    Alur: terima upload gambar -> OCR (EasyOCR) -> teks struk ->
    ekstraksi kategori + total. Import ocr ditunda agar server tetap bisa
    start walau model OCR belum terunduh.
    """
    try:
        from .ocr import read_image
    except ImportError:
        from ocr import read_image

    suffix = os.path.splitext(file.filename or "")[1] or ".png"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        text = read_image(tmp_path)
        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Tidak ada teks terbaca pada gambar struk.",
            )

        result = receipt_parser.parse(text)
        # jangan kirim raw_text yang panjang di respon API
        result.pop("raw_text", None)
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)