"""Explicit, one-time model download. Never called by the web server.

No credentials, no AI request, no automatic .env changes. Verify SHA-256 before
installing; do not overwrite an existing different model.
"""
import argparse
import hashlib
import shutil
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "Qwen3-4B-Q4_K_M.gguf"
URL = "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/" + NAME
SHA256 = "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5"
DEFAULT = ROOT / "models" / "downloads" / NAME


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(target):
    target = target.resolve()
    if target.exists():
        if checksum(target) != SHA256:
            raise FileExistsError("File tujuan sudah ada dengan isi berbeda; tidak ditimpa.")
        print("Model sudah ada dan checksum cocok.")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(target.parent).free < 3_000_000_000:
        raise OSError("Sediakan sedikitnya 3 GB ruang kosong untuk unduhan model.")
    temporary = None
    try:
        with urllib.request.urlopen(URL, timeout=30) as response, tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=NAME+".", suffix=".part", delete=False
        ) as handle:
            temporary = Path(handle.name)
            written = 0
            next_update = 100_000_000
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                handle.write(chunk)
                written += len(chunk)
                if written >= next_update:
                    print(f"Terunduh {written/1_000_000:.0f} MB…", flush=True)
                    next_update += 100_000_000
        if checksum(temporary) != SHA256:
            raise ValueError("Checksum tidak cocok; model tidak dipasang.")
        if target.exists():
            raise FileExistsError("Tujuan muncul saat unduhan berjalan; tidak ditimpa.")
        temporary.rename(target)
        temporary = None
        print("Model terpasang. Tambahkan ke .env:")
        print(f"LOCAL_LLM_PATH={target.as_posix()}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)  # only our own incomplete download


def main():
    parser = argparse.ArgumentParser(description="Pasang Qwen3 4B lokal; unduhan sekitar 2,5 GB, lisensi Apache-2.0.")
    parser.add_argument("--download", action="store_true", help="Unduh model resmi ke server/laptop ini.")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    if not args.download:
        print("Tidak ada unduhan otomatis. Untuk memasang model, jalankan: python setup_local_ai.py --download")
        print("Sumber/lisensi: https://huggingface.co/Qwen/Qwen3-4B-GGUF")
        return
    download(args.output)


if __name__ == "__main__":
    main()
