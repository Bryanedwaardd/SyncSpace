"""Tes end-to-end: file audio -> teks -> transaksi JSON."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from speech import transcribe          # noqa: E402
from predict import TransactionParser  # noqa: E402

audio = sys.argv[1] if len(sys.argv) > 1 else "sample_voice.wav"

text = transcribe(audio)
print("TEKS  :", repr(text))

result = TransactionParser().parse(text)
print("HASIL :", json.dumps(result, ensure_ascii=False))
