"""
Speech-to-text (voice -> teks) untuk money tracking NLP.

Menggunakan faster-whisper (Whisper OpenAI versi cepat) yang jalan OFFLINE
di komputer. Tidak butuh internet atau API key setelah model terunduh.

Alur lengkap:
    voice (wav/mp3/m4a)  ->  transcribe()  ->  teks  ->  TransactionParser

Model di-load sekali (lazy) lalu di-cache selama proses hidup, karena load
model relatif berat. Ukuran model bisa diatur lewat env var atau argumen.

Ukuran model (trade-off kecepatan vs akurasi):
    tiny   ~75MB   paling cepat, akurasi paling rendah  (default)
    base   ~145MB  ringan, cukup untuk kalimat pendek
    small  ~480MB  lebih akurat, agak lambat
    medium ~1.5GB  akurat, butuh RAM besar

Model 'tiny' sudah terunduh ke cache. Untuk ukuran lain, jalankan
'python src/download_model.py <ukuran>' (mendukung resume kalau koneksi lambat).
"""

import os
from functools import lru_cache

import av
import numpy as np
from faster_whisper import WhisperModel

# Whisper selalu bekerja pada audio 16kHz mono
_SAMPLE_RATE = 16000

# ukuran model default; bisa dioverride via env MONEYNLP_WHISPER_MODEL.
# "small" dipilih default karena akurasinya jauh lebih baik untuk Bahasa
# Indonesia (model "tiny" sering salah total). Sudah terunduh ke cache lokal.
DEFAULT_MODEL_SIZE = os.getenv("MONEYNLP_WHISPER_MODEL", "small")


@lru_cache(maxsize=2)
def _get_model(model_size: str) -> WhisperModel:
    """Load (dan cache) model Whisper. CPU int8 supaya ringan & tanpa GPU."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def _decode_audio(audio_path: str) -> np.ndarray:
    """Dekode file audio apa pun menjadi array float32 mono 16kHz.

    Dibuat manual dengan PyAV karena faster_whisper.decode_audio() bawaan
    tidak kompatibel dengan PyAV versi baru (parameter metadata_errors dihapus).
    Mendukung wav/mp3/m4a/ogg/flac selama PyAV/ffmpeg bisa membacanya.
    """
    resampler = av.audio.resampler.AudioResampler(
        format="s16", layout="mono", rate=_SAMPLE_RATE
    )
    chunks: list[np.ndarray] = []
    with av.open(audio_path, mode="r") as container:
        stream = container.streams.audio[0]
        for frame in container.decode(stream):
            for rframe in resampler.resample(frame):
                chunks.append(rframe.to_ndarray().reshape(-1))

    if not chunks:
        return np.zeros(0, dtype=np.float32)
    pcm16 = np.concatenate(chunks)
    return pcm16.astype(np.float32) / 32768.0


def transcribe(audio_path: str, model_size: str = DEFAULT_MODEL_SIZE) -> str:
    """Ubah file audio menjadi teks Bahasa Indonesia.

    Args:
        audio_path: path ke file audio (wav, mp3, m4a, ogg, dll).
        model_size: ukuran model whisper (tiny/base/small/medium).

    Returns:
        Teks hasil transkripsi (sudah di-strip spasi).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio tidak ditemukan: {audio_path}")

    model = _get_model(model_size)
    audio = _decode_audio(audio_path)   # numpy float32 mono 16kHz
    segments, _info = model.transcribe(
        audio,
        language="id",          # paksa Bahasa Indonesia
        beam_size=5,
        vad_filter=True,        # buang bagian hening biar lebih akurat
    )
    text = " ".join(seg.text for seg in segments)
    return text.strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Pemakaian: python src/speech.py <path_audio>")
        print("Contoh   : python src/speech.py sample.wav")
        sys.exit(1)

    hasil = transcribe(sys.argv[1])
    print("Teks hasil voice:", repr(hasil))
