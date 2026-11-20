"""
Unduh model Whisper ke cache lokal dengan RESUME + retry.

Berguna kalau koneksi ke Hugging Face sering putus di tengah download
(file model cukup besar). Script ini otomatis melanjutkan dari byte terakhir
yang sudah terunduh, jadi aman dijalankan berulang kali.

Pemakaian:
    python src/download_model.py            # default: model "base"
    python src/download_model.py tiny       # atau tiny / small / medium

Setelah selesai, faster-whisper akan otomatis memakai model dari cache ini
(tidak perlu download ulang) saat speech.py / API dijalankan.
"""

import sys
import time
from pathlib import Path

import urllib.request

# daftar file yang dibutuhkan faster-whisper per model
REPO = "Systran/faster-whisper-{size}"
FILES = ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"]
BASE_URL = "https://huggingface.co/{repo}/resolve/main/{fname}"

VALID_SIZES = {"tiny", "base", "small", "medium", "large-v3"}


def target_dir(size: str) -> Path:
    """Lokasi cache yang dibaca faster-whisper (local_files_only)."""
    home = Path.home()
    return (
        home / ".cache" / "huggingface" / "hub"
        / f"models--Systran--faster-whisper-{size}"
        / "snapshots" / "local"
    )


def download_with_resume(url: str, dest: Path, max_retries: int = 20) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")

    # ukuran total file di server
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        total = int(r.headers.get("Content-Length", 0))

    if dest.exists() and total and dest.stat().st_size == total:
        print(f"  [skip] {dest.name} sudah lengkap ({total/1e6:.1f} MB)")
        return

    for attempt in range(1, max_retries + 1):
        downloaded = part.stat().st_size if part.exists() else 0
        if total and downloaded >= total:
            break

        headers = {"Range": f"bytes={downloaded}-"} if downloaded else {}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp, open(part, "ab") as f:
                while True:
                    chunk = resp.read(1024 * 256)  # 256KB
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(
                            f"\r  {dest.name}: {downloaded/1e6:6.1f}/{total/1e6:.1f} MB "
                            f"({pct:5.1f}%)",
                            end="",
                            flush=True,
                        )
            print()
            break
        except Exception as e:  # noqa: BLE001 - lanjut retry apapun errornya
            wait = min(5 * attempt, 30)
            print(f"\n  [retry {attempt}/{max_retries}] putus: {e}. tunggu {wait}s...")
            time.sleep(wait)
    else:
        raise RuntimeError(f"Gagal mengunduh {dest.name} setelah {max_retries} percobaan")

    part.replace(dest)


def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else "base"
    if size not in VALID_SIZES:
        print(f"Ukuran '{size}' tidak dikenal. Pilih: {', '.join(sorted(VALID_SIZES))}")
        sys.exit(1)

    repo = REPO.format(size=size)
    out = target_dir(size)
    print(f"Mengunduh model '{size}' -> {out}")

    for fname in FILES:
        url = BASE_URL.format(repo=repo, fname=fname)
        download_with_resume(url, out / fname)

    # tandai ref main agar snapshot 'local' dipakai
    refs = out.parent.parent / "refs"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "main").write_text("local")

    print(f"\nSelesai. Model '{size}' siap dipakai dari cache lokal.")
    print("Set env MONEYNLP_WHISPER_MODEL sesuai ukuran ini jika bukan 'base'.")


if __name__ == "__main__":
    main()
