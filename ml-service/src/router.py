"""Pintu masuk teks: jadwal -> draf agenda, selain itu -> TransactionParser."""
from datetime import date

import joblib

from predict import MODEL_DIR, TransactionParser
from time_parser import parse_schedule
from train_intent import intent_text

LOW_CONF = 0.60


class AssistantParser:
    def __init__(self):
        self.intent_model = joblib.load(MODEL_DIR / "intent_model.joblib")
        self.tx = TransactionParser()

    def parse(self, text: str, today: date | None = None) -> dict:
        x = intent_text(text)
        proba = self.intent_model.predict_proba([x])[0]
        label = self.intent_model.classes_[proba.argmax()]
        conf = round(float(proba.max()), 4)

        if label == "jadwal":
            ev = parse_schedule(text, today)
            return {
                "text": text, "type": "jadwal", "event": ev,
                "confidence": {"type": conf},
                "needs_confirmation": ev["needs_confirmation"] or conf < LOW_CONF,
            }
        out = self.tx.parse(text)
        out["needs_confirmation"] = out["amount"] is None or conf < LOW_CONF
        return out


if __name__ == "__main__":
    import json
    ref = date(2026, 11, 18)
    p = AssistantParser()
    for s in ["tanggal 8 jam 8 sampai 10 ada rapat tim", "aku bayar listrik 25 ribu",
              "bayar listrik dua puluh lima ribu", "tanggal 25 bayar listrik 150rb",
              "ada rapat himpunan", "lusa jam setengah 8 praktikum database"]:
        print(json.dumps(p.parse(s, ref), ensure_ascii=False))