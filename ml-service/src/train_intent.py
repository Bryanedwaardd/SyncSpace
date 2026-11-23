"""Latih intent classifier 3 kelas: pengeluaran / pemasukan / jadwal.

Input model = teks yang SUDAH di-mask (ekspresi waktu -> 'tokwaktu'/'tokdate').
Jalankan dari folder src:  python train_intent.py
"""
import random
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline

from schedule_data import TEST_JADWAL, TEST_NON_JADWAL, make_jadwal_train
from time_parser import mask_time

BASE = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE / "models"


def intent_text(text: str) -> str:
    """mask waktu -> hapus angka/nominal -> huruf saja."""
    t = mask_time(text)
    t = re.sub(r"rp\.?", " ", t)
    t = re.sub(r"\d+([.,]\d+)*\s*(ribu|rb|juta|jt|miliar|k)?\b", " tokuang ", t)
    t = re.sub(r"[^a-z\s&]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def build_train_df(seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    tx = pd.read_csv(BASE / "data" / "transactions.csv")[["text", "type"]]
    tx = tx.rename(columns={"type": "intent"})
    rows = tx.to_dict("records")
    # hard negative: transaksi yang menyebut tanggal/jam. Tanpa ini model belajar
    # jalan pintas "ada tokwaktu => jadwal".
    aug = []
    for r in rows:
        if rng.random() < 0.5:
            pre = rng.choice(["tanggal 5 ", "tgl 25 ", "tadi jam 7 malam ", "kemarin ",
                              "tanggal 1 ", "hari senin ", "tadi pagi jam 8 ", "jam 2 siang "])
            aug.append({"text": pre + r["text"], "intent": r["intent"]})
    jad = [{"text": s, "intent": "jadwal"} for s in make_jadwal_train()]
    return pd.DataFrame(rows + aug + jad)


def pipe() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, C=10, class_weight="balanced")),
    ])


def rule_baseline(text: str) -> str:
    """Baseline: ada ekspresi waktu DAN tidak ada nominal uang -> jadwal."""
    m = mask_time(text)
    has_time = "tokwaktu" in m or "tokdate" in m
    has_money = bool(re.search(r"\d+\s*(ribu|rb|juta|jt|k)\b|rp\.?\s*\d", text.lower())) \
        or bool(re.search(r"\b\d{4,}\b", text))
    return "jadwal" if has_time and not has_money else "uang"


def main():
    df = build_train_df()
    print(df["intent"].value_counts(), "\n")
    model = pipe().fit(df["text"].map(intent_text), df["intent"])

    X = TEST_JADWAL + TEST_NON_JADWAL
    y = ["jadwal"] * len(TEST_JADWAL) + ["uang"] * len(TEST_NON_JADWAL)
    pred = [("jadwal" if p == "jadwal" else "uang") for p in model.predict([intent_text(s) for s in X])]
    base = [rule_baseline(s) for s in X]
    for name, p in (("MODEL", pred), ("BASELINE aturan", base)):
        print(f"== {name} ==")
        print(classification_report(y, p, zero_division=0))
        print(confusion_matrix(y, p, labels=["jadwal", "uang"]))
        bad = [(s, a) for s, a, b in zip(X, y, p) if a != b]
        print("salah:", *bad, sep="\n  ")
        print()
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "intent_model.joblib")


if __name__ == "__main__":
    main()