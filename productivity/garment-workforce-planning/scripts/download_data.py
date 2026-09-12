from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/597/productivity%2Bprediction%2Bof%2Bgarment%2Bemployees.zip"
FILENAME = "garments_worker_productivity.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    raw_dir = project / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / FILENAME

    with tempfile.TemporaryDirectory() as td:
        archive = Path(td) / "dataset.zip"
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as zf:
            candidates = [n for n in zf.namelist() if n.endswith(FILENAME)]
            if not candidates:
                raise FileNotFoundError(f"{FILENAME} not found in downloaded archive")
            with zf.open(candidates[0]) as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst)

    manifest = {
        "file": FILENAME,
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    }
    (raw_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
