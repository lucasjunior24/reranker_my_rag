"""1.4 Limpa os textos extraídos: data/interim -> data/processed/clean."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

INTERIM = Path("data/interim")
CLEAN = Path("data/processed/clean")


def remove_repeated_lines(pages: list[str], threshold: float = 0.5) -> list[str]:
    """Remove linhas que aparecem em mais de `threshold` das páginas (cabeçalho/rodapé)."""
    if len(pages) < 4:  # poucos documentos de poucas páginas: a estatística não vale
        return pages
    counts = Counter(
        line.strip() for p in pages for line in set(p.splitlines()) if line.strip()
    )
    limit = threshold * len(pages)
    repeated = {line for line, c in counts.items() if c > limit}
    return [
        "\n".join(l for l in p.splitlines() if l.strip() not in repeated) for p in pages
    ]


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # hifenização
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.M)  # nº de página sozinho
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # quebra simples vira espaço
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_all(min_chars: int = 50) -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    for path in sorted(INTERIM.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        raw_pages = remove_repeated_lines([p["text"] for p in doc["pages"]])
        pages = []
        for p, text in zip(doc["pages"], raw_pages):
            text = clean_text(text)
            if len(text) >= min_chars:  # descarta páginas quase vazias
                pages.append({"page": p["page"], "text": text})
        (CLEAN / path.name).write_text(
            json.dumps({"doc_id": doc["doc_id"], "pages": pages}, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[OK] {doc['doc_id']}: {len(pages)}/{len(doc['pages'])} páginas mantidas")


if __name__ == "__main__":
    clean_all()
