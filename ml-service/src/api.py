"""
REST API ML service untuk money tracking + jadwal (format kontrak dengan backend).

Jalankan (dari folder ml-service):
    python -m uvicorn api:app --app-dir src --port 8000

Endpoint (semua mengembalikan JSON dengan bentuk yang sama):
    POST /api/v1/parse/text    body: {"text": "Beli kopi 25rb"}
    POST /api/v1/parse/voice   form-data: file=<audio wav/mp3/m4a/ogg>
    POST /api/v1/parse/image   form-data: file=<gambar struk jpg/png>
    GET  /health

Respon:
    {
        "intent": "EXPENSE",              # EXPENSE | INCOME | SCHEDULE
        "category": "Food & Beverage",    # null untuk SCHEDULE
        "amount": 25000,                  # null bila nominal tidak ketemu
        "extracted_text": "Beli kopi 25rb",
        "needs_confirmation": false,      # true -> minta user konfirmasi
        "event": null                     # objek agenda bila intent SCHEDULE
    }

Alur: teks / suara (-> teks lewat Whisper) -> AssistantParser (jadwal atau
transaksi). Gambar struk -> OCR -> ReceiptParser. Hasil internal (label
Indonesia) diterjemahkan ke format kontrak oleh contract.py.

Data suara dan gambar hanya disimpan sebagai file sementara selama diproses,
lalu langsung dihapus.
"""

import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

try:
    from .contract import from_assistant, from_receipt
    from .receipt_parser import ReceiptParser
    from .router import AssistantParser
except ImportError:
    from contract import from_assistant, from_receipt
    from receipt_parser import ReceiptParser
    from router import AssistantParser

app = FastAPI(title="Money Tracking NLP API", version="2.0.0")

# load model sekali saat startup (di-cache selama proses hidup)
assistant = AssistantParser()          # router: jadwal vs transaksi
receipt_parser = ReceiptParser()


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    intent: str
    category: str | None
    amount: int | None
    extracted_text: str
    needs_confirmation: bool = False
    event: dict | None = None


async def _save_upload(file: UploadFile, default_suffix: str) -> str:
    """Simpan upload ke file sementara (Whisper dan OCR butuh path file)."""
    suffix = os.path.splitext(file.filename or "")[1] or default_suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        return tmp.name


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/api/v1/parse/text", response_model=ParseResponse)
def parse_text(req: ParseRequest):
    """Teks bebas -> otomatis dideteksi: transaksi ATAU jadwal."""
    return from_assistant(assistant.parse(req.text), req.text)


@app.post("/api/v1/parse/voice", response_model=ParseResponse)
async def parse_voice(file: UploadFile = File(...)):
    """Audio -> teks (Whisper) -> transaksi atau jadwal.

    Import speech ditunda ke dalam fungsi agar server tetap bisa start walau
    model whisper belum terunduh.
    """
    try:
        from .speech import transcribe
    except ImportError:
        from speech import transcribe

    tmp_path = None
    try:
        tmp_path = await _save_upload(file, ".wav")
        text = transcribe(tmp_path)
        if not text:
            raise HTTPException(
                status_code=422, detail="Tidak ada ucapan terdeteksi pada audio."
            )
        return from_assistant(assistant.parse(text), text)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/v1/parse/image", response_model=ParseResponse)
async def parse_image(file: UploadFile = File(...)):
    """Gambar struk -> OCR -> kategori + total.

    Import ocr ditunda agar server tetap bisa start walau model OCR belum
    terunduh.
    """
    try:
        from .ocr import read_image
    except ImportError:
        from ocr import read_image

    tmp_path = None
    try:
        tmp_path = await _save_upload(file, ".png")
        text = read_image(tmp_path)
        if not text.strip():
            raise HTTPException(
                status_code=422, detail="Tidak ada teks terbaca pada gambar struk."
            )
        return from_receipt(receipt_parser.parse(text))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)