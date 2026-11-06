"""1.2 Baixa os documentos listados em data/sources.csv para data/raw/{doc_id}.{formato}."""
import hashlib
from pathlib import Path

import httpx
import pandas as pd

RAW = Path("data/raw")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download_all(sources_csv: str = "data/sources.csv") -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(sources_csv, dtype=str).fillna("")
    hashes = []
    for row in df.itertuples():
        dest = RAW / f"{row.doc_id}.{row.formato}"
        if not dest.exists():
            try:
                r = httpx.get(row.url, timeout=60, follow_redirects=True)
                r.raise_for_status()
                dest.write_bytes(r.content)
            except httpx.HTTPError as e:
                print(f"[ERRO] {row.doc_id}: {e}")
                hashes.append("")
                continue
        hashes.append(sha256_of(dest))
    df["sha256"] = hashes

    dups = df[(df.sha256 != "") & df.duplicated("sha256", keep=False)]
    if not dups.empty:
        print("[AVISO] Arquivos duplicados (mesmo hash):")
        print(dups[["doc_id", "sha256"]].to_string(index=False))

    df.to_csv(sources_csv, index=False)


if __name__ == "__main__":
    download_all()
