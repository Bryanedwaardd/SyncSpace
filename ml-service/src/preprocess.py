"""Preprocessing gambar struk sebelum OCR: luruskan (deskew), crop, perjelas."""
import cv2
import numpy as np


def _paper_mask(gray: np.ndarray):
    """Mask kertas struk (area terang terbesar), lubang teks sudah ditutup."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, m = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 0.10 * gray.size:   # tidak ada kertas yang jelas
        return None
    filled = np.zeros_like(gray)
    cv2.drawContours(filled, [c], -1, 255, -1)  # isi penuh, teks ikut masuk
    return filled


def _rotate(img: np.ndarray, angle: float, border=cv2.BORDER_REPLICATE):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=border)


def estimate_skew(gray: np.ndarray, max_angle: float = 15, step: float = 0.5) -> float:
    """Cari sudut putar yang membuat baris teks paling rata horizontal.

    Idenya: kalau teks lurus, jumlah piksel tinta per baris-piksel punya
    puncak dan lembah tajam (baris teks vs celah antar baris). Kalau miring,
    puncaknya melebar. Kita coba banyak sudut dan pilih yang paling tajam.
    """
    scale = 800 / max(gray.shape)
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    paper = _paper_mask(small)
    blur = cv2.GaussianBlur(small, (3, 3), 0)
    ink = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 31, 15)
    if paper is not None:
        inner = cv2.erode(paper, np.ones((15, 15), np.uint8))  # jauhi tepi kertas
        ink = cv2.bitwise_and(ink, inner)

    best_angle, best_score = 0.0, -1.0
    for a in np.arange(-max_angle, max_angle + 1e-9, step):
        rows = _rotate(ink, a, cv2.BORDER_CONSTANT).sum(axis=1).astype(np.float64)
        score = np.var(rows)
        if score > best_score:
            best_angle, best_score = float(a), score
    return best_angle


def deskew_and_crop(rgb: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    angle = estimate_skew(gray)
    if abs(angle) > 0.3:
        rgb = _rotate(rgb, angle)

    # crop ke area kertas supaya latar (meja, dll.) tidak ikut dibaca OCR
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    paper = _paper_mask(gray)
    if paper is not None:
        x, y, w, h = cv2.boundingRect(paper)
        pad = 10
        y0, y1 = max(0, y - pad), min(rgb.shape[0], y + h + pad)
        x0, x1 = max(0, x - pad), min(rgb.shape[1], x + w + pad)
        rgb = rgb[y0:y1, x0:x1]
    return rgb


def preprocess(rgb: np.ndarray, mode: str = "clahe") -> np.ndarray:
    """mode: raw | gray | clahe | adaptive"""
    if mode == "raw":
        return rgb

    rgb = deskew_and_crop(rgb)

    # perbesar kalau gambar kecil: huruf kecil = sulit dibaca OCR
    h, w = rgb.shape[:2]
    target = 1600
    if max(h, w) < target:
        s = target / max(h, w)
        rgb = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if mode == "gray":
        return gray

    gray = cv2.medianBlur(gray, 3)

    if mode == "clahe":
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    if mode == "adaptive":
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 15,
        )
    raise ValueError(f"mode tidak dikenal: {mode}")