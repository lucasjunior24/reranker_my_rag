"""1.5 Chunking por tokens do tokenizer do modelo de embeddings.

Uso: python -m src.chunking.chunk --size 512 --overlap 64
Para comparar tamanhos, use --out diferente (ex.: data/processed/chunks_256.jsonl).
Registre a escolha final e o motivo em experiments/chunking.md.
"""
import argparse
import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

MODEL = "intfloat/multilingual-e5-base"


def chunk_corpus(
    clean_dir: str = "data/processed/clean",
    out: str = "data/processed/chunks.jsonl",
    size: int = 512,
    overlap: int = 64,
    model: str = MODEL,
) -> int:
    tokenizer = AutoTokenizer.from_pretrained(model)
    # E5 tem limite de 512 tokens e usa ~10 para prefixo/especiais
    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer,
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    n = 0
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for path in sorted(Path(clean_dir).glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            for page in doc["pages"]:
                for i, chunk in enumerate(splitter.split_text(page["text"])):
                    rec = {
                        "chunk_id": f'{doc["doc_id"]}_p{page["page"]}_c{i}',
                        "doc_id": doc["doc_id"],
                        "page": page["page"],
                        "text": chunk,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--overlap", type=int, default=64)
    ap.add_argument("--out", default="data/processed/chunks.jsonl")
    ap.add_argument("--model", default=MODEL)
    a = ap.parse_args()
    print(f"{chunk_corpus(out=a.out, size=a.size, overlap=a.overlap, model=a.model)} chunks")
