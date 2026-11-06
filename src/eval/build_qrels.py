"""1.7 Monta data/eval/qrels.jsonl a partir de:
- data/eval/candidates.jsonl (sintéticas; só entram as com "aprovada": true)
- data/eval/manual.jsonl (escritas à mão; campos: question, answer, relevant_chunks)

O split de cada pergunta manual é inferido do doc_id do primeiro chunk relevante.
Valida que todos os chunk_id existem em chunks.jsonl.
"""
import json
from pathlib import Path

from src.eval.generate_questions import load_chunks
from src.ingest.split import doc_to_split


def read_jsonl(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def build(out: str = "data/eval/qrels.jsonl") -> None:
    chunk_doc = {c["chunk_id"]: c["doc_id"] for c in load_chunks()}
    split_of = doc_to_split()

    items = []
    for c in read_jsonl("data/eval/candidates.jsonl"):
        if c.get("aprovada") is True:
            items.append({**c, "origin": "sintetica"})
    for m in read_jsonl("data/eval/manual.jsonl"):
        items.append({**m, "origin": "manual"})

    final = []
    for it in items:
        missing = [c for c in it["relevant_chunks"] if c not in chunk_doc]
        if missing:
            print(f"[AVISO] chunk inexistente, pergunta ignorada: {missing} | {it['question']}")
            continue
        it["split"] = split_of[chunk_doc[it["relevant_chunks"][0]]]
        it.pop("aprovada", None)
        final.append(it)

    for i, it in enumerate(final):
        it["qid"] = f"q{i:04d}"
    with open(out, "w", encoding="utf-8") as f:
        for it in final:
            f.write(json.dumps(
                {k: it[k] for k in ("qid", "question", "answer", "relevant_chunks", "origin", "split")},
                ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"{len(final)} perguntas ->", dict(Counter((i["split"], i["origin"]) for i in final)))


if __name__ == "__main__":
    build()
