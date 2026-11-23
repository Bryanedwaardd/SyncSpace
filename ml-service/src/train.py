"""
Training model NLP untuk money tracking (Bahasa Indonesia).

Membuat dua classifier berbasis TF-IDF + Linear SVM:
  1. type_model     -> prediksi "pemasukan" / "pengeluaran"
  2. category_model -> prediksi kategori (Makanan & Minuman, Transport, Gaji, ...)

Model disimpan sebagai file .joblib di folder models/ supaya bisa dipakai backend.

Jalankan:
    python src/train.py
"""

import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "transactions.csv"
MODEL_DIR = BASE_DIR / "models"


def clean_text(text: str) -> str:
    """Normalisasi teks: lowercase, hapus angka/nominal, rapikan spasi.

    Angka dibuang supaya model fokus pada kata kunci (jenis & kategori),
    bukan pada nominal yang ditangani terpisah oleh amount_parser.
    """
    t = str(text).lower()
    t = re.sub(r"rp\.?", " ", t)
    t = re.sub(r"\d+([.,]\d+)*\s*(ribu|rb|juta|jt|miliar|milyar|k)?\b", " ", t)
    t = re.sub(r"[^a-z\s&]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(max_iter=1000, C=10, class_weight="balanced"),
            ),
        ]
    )


def train_one(name: str, X, y) -> Pipeline:
    print(f"\n=== Melatih model: {name} ===")
    # stratify agar tiap label terwakili; butuh minimal 2 sampel per kelas
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))

    # latih ulang pada seluruh data untuk model final
    pipe.fit(X, y)
    return pipe


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "type", "category"])
    df["clean"] = df["text"].apply(clean_text)

    print(f"Total data: {len(df)}")
    print("Distribusi type:\n", df["type"].value_counts())
    print("\nDistribusi category:\n", df["category"].value_counts())

    X = df["clean"]

    type_model = train_one("type", X, df["type"])
    category_model = train_one("category", X, df["category"])

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(type_model, MODEL_DIR / "type_model.joblib")
    joblib.dump(category_model, MODEL_DIR / "category_model.joblib")
    print(f"\nModel tersimpan di: {MODEL_DIR}")


if __name__ == "__main__":
    main()
