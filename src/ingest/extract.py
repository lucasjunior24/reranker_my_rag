"""1.3 Extrai texto por página (com OCR quando o PDF é escaneado) para data/interim/{doc_id}.json."""
import json
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
from bs4 import BeautifulSoup

RAW = Path("data/raw")
INTERIM = Path("data/interim")


def needs_ocr(pdf_path: Path, min_chars: int = 50) -> bool:
    with fitz.open(pdf_path) as doc:
        empty = sum(1 for p in doc if len(p.get_text().strip()) < min_chars)
        return empty / max(len(doc), 1) > 0.5


def extract_pdf(pdf_path: Path) -> list[dict]:
    src = pdf_path
    if needs_ocr(pdf_path):
        src = INTERIM / f"{pdf_path.stem}.ocr.pdf"
        # --skip-text: só roda OCR nas páginas sem texto
        subprocess.run(
            ["ocrmypdf", "-l", "por", "--skip-text", str(pdf_path), str(src)],
            check=True,
        )
    with fitz.open(src) as doc:
        return [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]


def extract_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return [{"page": 1, "text": soup.get_text("\n")}]


def extract_txt(path: Path) -> list[dict]:
    return [{"page": 1, "text": path.read_text(encoding="utf-8", errors="ignore")}]


EXTRACTORS = {".pdf": extract_pdf, ".html": extract_html, ".htm": extract_html, ".txt": extract_txt}


def extract_all(force: bool = False) -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)
    for path in sorted(RAW.iterdir()):
        fn = EXTRACTORS.get(path.suffix.lower())
        if fn is None:
            continue
        out = INTERIM / f"{path.stem}.json"
        if out.exists() and not force:
            continue
        try:
            pages = fn(path)
        except Exception as e:  # um documento ruim não deve parar o lote
            print(f"[ERRO] {path.name}: {e}")
            continue
        out.write_text(
            json.dumps({"doc_id": path.stem, "pages": pages}, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[OK] {path.name}: {len(pages)} página(s)")


if __name__ == "__main__":
    extract_all()
